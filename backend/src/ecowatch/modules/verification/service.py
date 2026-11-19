"""Service layer for indicators, verification assessments, and publications."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.phase3Contracts import record_event, require_permission, require_text
from ecowatch.modules.phase3Reads import list_page, read_scope, scope_statement
from ecowatch.modules.verification import enums, models, rules
from ecowatch.modules.verification.schemas import (
    AssessmentResponse,
    IndicatorResponse,
    MeasurementResponse,
    PublicationResponse,
)


class VerificationService:
    """Manage qualified measurements and gated outcome verification."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_indicator_definition(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        code: str,
        name: str,
        domain: str,
        unitId: UUID,
        methodName: str,
        methodVersion: str,
        description: str | None = None,
        criteriaVersion: str | None = None,
        requestId: str | None = None,
    ) -> models.IndicatorDefinition:
        """Create an approved indicator definition with a resolved unit."""
        require_permission(principal, Permission.VERIFICATION_APPROVE, organisationId)
        for fieldName, value in {
            "code": code,
            "name": name,
            "domain": domain,
            "methodName": methodName,
            "methodVersion": methodVersion,
        }.items():
            require_text(value, fieldName)
        duplicate = self._session.scalar(
            select(models.IndicatorDefinition.id).where(
                models.IndicatorDefinition.organisationId == organisationId,
                models.IndicatorDefinition.code == code,
            )
        )
        if duplicate is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "An indicator with this code already exists.",
                field="code",
            )
        record = models.IndicatorDefinition(
            organisationId=organisationId,
            code=code.strip(),
            name=name.strip(),
            domain=domain.strip(),
            description=description,
            unitId=unitId,
            methodName=methodName.strip(),
            methodVersion=methodVersion.strip(),
            criteriaVersion=criteriaVersion,
            approvedByUserId=principal.userId,
            approvedAt=utc_now(),
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.indicator.created",
            targetType="indicatorDefinition",
            targetId=record.id,
            detail={"code": record.code},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def record_measurement(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        indicatorDefinitionId: UUID,
        measuredAt: datetime,
        qualifier: str | enums.MeasurementQualifier,
        unitId: UUID,
        methodName: str,
        methodVersion: str,
        value: float | None = None,
        detectionLimit: float | None = None,
        interventionId: UUID | None = None,
        caseId: UUID | None = None,
        observationId: UUID | None = None,
        qualityControls: str | None = None,
        uncertaintyNote: str | None = None,
        source: str | None = None,
        requestId: str | None = None,
    ) -> models.IndicatorMeasurement:
        """Record a measurement only with a resolved unit, method, and time."""
        require_permission(principal, Permission.VERIFICATION_WRITE, organisationId)
        if interventionId is None and caseId is None and observationId is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A measurement must link to an intervention, case, or observation.",
                field="interventionId",
            )
        rules.assert_measurement_valid(
            value=value,
            qualifier=qualifier,
            detectionLimit=detectionLimit,
            unitId=unitId,
            methodName=methodName,
            methodVersion=methodVersion,
            measuredAt=measuredAt,
        )
        definition = self._session.get(models.IndicatorDefinition, indicatorDefinitionId)
        if definition is None or definition.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Indicator definition not found.",
                statusCode=404,
                field="indicatorDefinitionId",
            )
        qualifierValue = rules.require_enum(
            enums.MeasurementQualifier, qualifier, "qualifier"
        )
        record = models.IndicatorMeasurement(
            organisationId=organisationId,
            indicatorDefinitionId=indicatorDefinitionId,
            interventionId=interventionId,
            caseId=caseId,
            observationId=observationId,
            measuredAt=measuredAt,
            value=Decimal(str(value)) if value is not None else None,
            qualifier=qualifierValue.value,
            detectionLimit=(
                Decimal(str(detectionLimit)) if detectionLimit is not None else None
            ),
            unitId=unitId,
            methodName=methodName.strip(),
            methodVersion=methodVersion.strip(),
            qualityControls=qualityControls,
            uncertaintyNote=uncertaintyNote,
            source=source,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.measurement.recorded",
            targetType="indicatorMeasurement",
            targetId=record.id,
            requestId=requestId,
        )
        self._session.commit()
        return record

    def create_assessment(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        interventionId: UUID,
        baselineMeasurementIds: list[str],
        followUpMeasurementIds: list[str],
        comparisonMethod: str,
        baselineValues: list[float],
        followUpValues: list[float],
        direction: str | enums.ExpectedDirection,
        minimumDetectableChange: float | None = None,
        uncertainty: float | None = None,
        confounders: str | None = None,
        seasonalityNotes: str | None = None,
        uncertaintyNote: str | None = None,
        criteriaVersion: str | None = None,
        requestId: str | None = None,
    ) -> models.VerificationAssessment:
        """Create a draft assessment that can never itself claim recovery."""
        require_permission(principal, Permission.VERIFICATION_WRITE, organisationId)
        require_text(comparisonMethod, "comparisonMethod")
        conclusion = rules.assess_observed_change(
            baselineValues=baselineValues,
            followUpValues=followUpValues,
            direction=direction,
            minimumDetectableChange=minimumDetectableChange,
            uncertainty=uncertainty,
        )
        record = models.VerificationAssessment(
            organisationId=organisationId,
            interventionId=interventionId,
            baselineMeasurementIds=baselineMeasurementIds,
            followUpMeasurementIds=followUpMeasurementIds,
            comparisonMethod=comparisonMethod.strip(),
            confounders=confounders,
            seasonalityNotes=seasonalityNotes,
            uncertaintyNote=uncertaintyNote,
            conclusion=conclusion.value,
            criteriaVersion=criteriaVersion,
            status=enums.AssessmentStatus.DRAFT.value,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.assessment.created",
            targetType="verificationAssessment",
            targetId=record.id,
            detail={"conclusion": record.conclusion},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def finalise_assessment(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        assessmentId: UUID,
        requestId: str | None = None,
    ) -> models.VerificationAssessment:
        """Finalise a draft assessment; recovery must use the dedicated gate."""
        require_permission(principal, Permission.VERIFICATION_APPROVE, organisationId)
        record = self._session.get(models.VerificationAssessment, assessmentId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Verification assessment not found.",
                statusCode=404,
                field="assessmentId",
            )
        if record.status != enums.AssessmentStatus.DRAFT.value:
            raise DomainError(
                ErrorCode.CONFLICT,
                "Only draft assessments can be finalised.",
                field="status",
            )
        if record.conclusion == enums.OutcomeConclusion.RECOVERY_VERIFIED.value:
            raise DomainError(
                ErrorCode.RECOVERY_NOT_VERIFIABLE,
                "Recovery verification must use verifyRecovery with approved criteria.",
                field="conclusion",
            )
        rules.assert_criteria_documented(record.criteriaVersion)
        record.status = enums.AssessmentStatus.FINAL.value
        record.reviewedByUserId = principal.userId
        record.reviewedAt = utc_now()
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.assessment.finalised",
            targetType="verificationAssessment",
            targetId=record.id,
            requestId=requestId,
        )
        self._session.commit()
        return record

    def verify_recovery(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        assessmentId: UUID,
        criteriaVersion: str,
        criteriaApproved: bool,
        comparisonMethod: str,
        uncertaintyDocumented: str,
        confoundersDocumented: str,
        seasonalContextDocumented: str,
        requestId: str | None = None,
    ) -> models.VerificationAssessment:
        """Verify recovery only with approved criteria and a specialist reviewer."""
        require_permission(principal, Permission.VERIFICATION_APPROVE, organisationId)
        record = self._session.get(models.VerificationAssessment, assessmentId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Verification assessment not found.",
                statusCode=404,
                field="assessmentId",
            )
        rules.assert_recovery_verification_allowed(
            criteriaVersion=criteriaVersion,
            criteriaApproved=criteriaApproved,
            reviewerRoles=frozenset(principal.roles_for_org(organisationId)),
            baselineMeasurementIds=record.baselineMeasurementIds,
            followUpMeasurementIds=record.followUpMeasurementIds,
            comparisonMethod=comparisonMethod,
            uncertaintyDocumented=uncertaintyDocumented,
            confoundersDocumented=confoundersDocumented,
            seasonalContextDocumented=seasonalContextDocumented,
        )
        record.conclusion = enums.OutcomeConclusion.RECOVERY_VERIFIED.value
        record.criteriaVersion = criteriaVersion.strip()
        record.status = enums.AssessmentStatus.FINAL.value
        record.reviewedByUserId = principal.userId
        record.reviewedAt = utc_now()
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.recovery.verified",
            targetType="verificationAssessment",
            targetId=record.id,
            requestId=requestId,
        )
        self._session.commit()
        return record

    def publish_summary(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        publishedText: str,
        verificationAssessmentId: UUID | None = None,
        caseId: UUID | None = None,
        requestId: str | None = None,
    ) -> models.Publication:
        """Publish an approved summary with a recorded authorised role."""
        require_permission(principal, Permission.PUBLICATION_WRITE, organisationId)
        approvedRole = principal.primary_role_label
        approvedAt = utc_now()
        rules.assert_publication_allowed(
            publishedText=publishedText,
            approvedByUserId=principal.userId,
            approvedRole=approvedRole,
            approvedAt=approvedAt,
        )
        record = models.Publication(
            organisationId=organisationId,
            verificationAssessmentId=verificationAssessmentId,
            caseId=caseId,
            publishedText=publishedText.strip(),
            approvedByUserId=principal.userId,
            approvedRole=approvedRole,
            approvedAt=approvedAt,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.publication.approved",
            targetType="publication",
            targetId=record.id,
            requestId=requestId,
        )
        self._session.commit()
        return record

    def retract_publication(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        publicationId: UUID,
        reason: str,
        requestId: str | None = None,
    ) -> models.Publication:
        """Retract a publication with a recorded reason."""
        require_permission(principal, Permission.PUBLICATION_WRITE, organisationId)
        record = self._session.get(models.Publication, publicationId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Publication not found.",
                statusCode=404,
                field="publicationId",
            )
        if record.retractedAt is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "Publication is already retracted.",
                field="retractedAt",
            )
        require_text(reason, "retractionReason")
        record.retractedAt = utc_now()
        record.retractionReason = reason.strip()
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="verification.publication.retracted",
            targetType="publication",
            targetId=record.id,
            requestId=requestId,
        )
        self._session.commit()
        return record

    def list_indicators(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[IndicatorResponse]:
        """List approved indicator definitions with their documented criteria."""
        allowedOrgIds = read_scope(principal, Permission.VERIFICATION_READ)
        stmt = scope_statement(
            select(models.IndicatorDefinition),
            models.IndicatorDefinition,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.IndicatorDefinition, cursor=cursor, limit=limit
        )
        return CursorPage[IndicatorResponse](
            items=[IndicatorResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_measurements(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[MeasurementResponse]:
        """List qualified measurements, never filling in censored values."""
        allowedOrgIds = read_scope(principal, Permission.VERIFICATION_READ)
        stmt = scope_statement(
            select(models.IndicatorMeasurement),
            models.IndicatorMeasurement,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.IndicatorMeasurement, cursor=cursor, limit=limit
        )
        return CursorPage[MeasurementResponse](
            items=[MeasurementResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_assessments(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[AssessmentResponse]:
        """List outcome assessments; only an authorised human sets recovery verified."""
        allowedOrgIds = read_scope(principal, Permission.VERIFICATION_READ)
        stmt = scope_statement(
            select(models.VerificationAssessment),
            models.VerificationAssessment,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.VerificationAssessment, cursor=cursor, limit=limit
        )
        return CursorPage[AssessmentResponse](
            items=[AssessmentResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_publications(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[PublicationResponse]:
        """List approved public text with its retraction state, not public-facing output."""
        allowedOrgIds = read_scope(principal, Permission.VERIFICATION_READ)
        stmt = scope_statement(
            select(models.Publication), models.Publication, allowedOrgIds, organisationId
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.Publication, cursor=cursor, limit=limit
        )
        return CursorPage[PublicationResponse](
            items=[PublicationResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )
