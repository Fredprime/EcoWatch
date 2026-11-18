"""Service layer for evidence-honest prioritisation assessments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.phase3Contracts import record_event, require_permission, require_text
from ecowatch.modules.prioritisation import enums, models, rules


class PrioritisationService:
    """Record prioritisation factors, missing inputs, and human decisions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_assessment(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        caseId: UUID,
        methodName: str,
        methodVersion: str,
        factors: dict[str, Any],
        assessmentAt: datetime | None = None,
        compositeRank: float | None = None,
        rankingMethodRef: str | None = None,
        rankIsNotSeverity: bool | None = None,
        requestId: str | None = None,
    ) -> models.PrioritisationAssessment:
        """Store only explicit factors and report missing inputs without imputation."""
        require_permission(principal, Permission.PRIORITISATION_WRITE, organisationId)
        require_text(methodName, "methodName")
        require_text(methodVersion, "methodVersion")
        factorView = rules.assert_assessment_honest(
            factors=factors,
            compositeRank=compositeRank,
            rankingMethodRef=rankingMethodRef,
            rankIsNotSeverity=rankIsNotSeverity,
            decision=None,
            rationale=None,
            decidedByUserId=None,
        )
        record = models.PrioritisationAssessment(
            organisationId=organisationId,
            caseId=caseId,
            assessmentAt=assessmentAt or utc_now(),
            methodName=methodName.strip(),
            methodVersion=methodVersion.strip(),
            factors=factorView["values"],
            missingInputs=factorView["missing"],
            compositeRank=Decimal(str(compositeRank)) if compositeRank is not None else None,
            rankingMethodRef=rankingMethodRef,
            rankIsNotSeverity=rankIsNotSeverity,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="prioritisation.assessment.created",
            targetType="prioritisationAssessment",
            targetId=record.id,
            requestId=requestId,
        )
        return record

    def record_decision(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        assessmentId: UUID,
        decision: str | enums.PriorityDecision,
        rationale: str,
        requestId: str | None = None,
    ) -> models.PrioritisationAssessment:
        """Record one accountable human decision per assessment."""
        require_permission(principal, Permission.PRIORITISATION_WRITE, organisationId)
        record = self._session.get(models.PrioritisationAssessment, assessmentId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Prioritisation assessment not found.",
                statusCode=404,
                field="assessmentId",
            )
        if record.decision is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A priority decision is already recorded; create a new assessment to revise it.",
                field="decision",
            )
        rules.assert_assessment_honest(
            factors=record.factors,
            compositeRank=(
                float(record.compositeRank) if record.compositeRank is not None else None
            ),
            rankingMethodRef=record.rankingMethodRef,
            rankIsNotSeverity=record.rankIsNotSeverity,
            decision=decision,
            rationale=rationale,
            decidedByUserId=principal.userId,
        )
        try:
            resolvedDecision = enums.PriorityDecision(decision)
        except ValueError as error:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Unsupported priority decision.",
                field="decision",
            ) from error
        record.decision = resolvedDecision.value
        record.decisionRationale = rationale.strip()
        record.decidedByUserId = principal.userId
        record.decidedAt = utc_now()
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="prioritisation.decision.recorded",
            targetType="prioritisationAssessment",
            targetId=record.id,
            detail={"decision": record.decision},
            requestId=requestId,
        )
        return record
