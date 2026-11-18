"""Service layer for authorised interventions and delivery milestones."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.interventions import enums, models, rules
from ecowatch.modules.phase3Contracts import record_event, require_permission, require_text


class InterventionsService:
    """Create and progress interventions without conflating activity and outcome."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_intervention(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        caseId: UUID,
        objective: str,
        responsibleOrganisationId: UUID,
        authorisedLeadUserId: UUID,
        plannedStartAt: datetime | None = None,
        plannedEndAt: datetime | None = None,
        rationale: str | None = None,
        approvalReference: str | None = None,
        location: Any | None = None,
        affectedAreaNotes: str | None = None,
        intendedOutcome: str | None = None,
        indicatorDefinitionIds: list[str] | None = None,
        baselineSummary: str | None = None,
        risks: str | None = None,
        limitations: str | None = None,
        followUpSchedule: str | None = None,
        additionalCaseIds: list[str] | None = None,
        requestId: str | None = None,
    ) -> models.Intervention:
        """Create a proposed intervention with an accountable owner and lead."""
        require_permission(principal, Permission.INTERVENTION_WRITE, organisationId)
        rules.assert_intervention_basics(
            objective=objective,
            responsibleOrganisationId=responsibleOrganisationId,
            authorisedLeadUserId=authorisedLeadUserId,
            plannedStartAt=plannedStartAt,
            plannedEndAt=plannedEndAt,
        )
        record = models.Intervention(
            organisationId=organisationId,
            caseId=caseId,
            additionalCaseIds=additionalCaseIds or [],
            objective=objective.strip(),
            rationale=rationale,
            responsibleOrganisationId=responsibleOrganisationId,
            authorisedLeadUserId=authorisedLeadUserId,
            approvalReference=approvalReference,
            location=location,
            affectedAreaNotes=affectedAreaNotes,
            plannedStartAt=plannedStartAt,
            plannedEndAt=plannedEndAt,
            status=enums.InterventionStatus.PROPOSED.value,
            intendedOutcome=intendedOutcome,
            indicatorDefinitionIds=indicatorDefinitionIds or [],
            baselineSummary=baselineSummary,
            risks=risks,
            limitations=limitations,
            followUpSchedule=followUpSchedule,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="interventions.intervention.created",
            targetType="intervention",
            targetId=record.id,
            requestId=requestId,
        )
        return record

    def add_milestone(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        interventionId: UUID,
        name: str,
        plannedAt: datetime | None = None,
        description: str | None = None,
        evidenceAssetIds: list[str] | None = None,
        requestId: str | None = None,
    ) -> models.InterventionMilestone:
        """Add a planned delivery milestone to an intervention."""
        require_permission(principal, Permission.INTERVENTION_WRITE, organisationId)
        parent = self._get_intervention(organisationId, interventionId)
        require_text(name, "name")
        record = models.InterventionMilestone(
            interventionId=parent.id,
            name=name.strip(),
            description=description,
            plannedAt=plannedAt,
            status=enums.MilestoneStatus.PLANNED.value,
            evidenceAssetIds=evidenceAssetIds or [],
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="interventions.milestone.created",
            targetType="interventionMilestone",
            targetId=record.id,
            requestId=requestId,
        )
        return record

    def complete_milestone(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        milestoneId: UUID,
        evidenceAssetIds: list[str] | None = None,
        requestId: str | None = None,
    ) -> models.InterventionMilestone:
        """Complete a milestone and derive at most an activity status."""
        require_permission(principal, Permission.INTERVENTION_WRITE, organisationId)
        milestone = self._session.get(models.InterventionMilestone, milestoneId)
        if milestone is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Milestone not found.",
                statusCode=404,
                field="milestoneId",
            )
        parent = self._get_intervention(organisationId, milestone.interventionId)
        if milestone.status == enums.MilestoneStatus.COMPLETED.value:
            raise DomainError(
                ErrorCode.CONFLICT, "Milestone is already completed.", field="status"
            )
        milestone.status = enums.MilestoneStatus.COMPLETED.value
        milestone.completedAt = utc_now()
        if evidenceAssetIds:
            milestone.evidenceAssetIds = sorted(
                {*milestone.evidenceAssetIds, *evidenceAssetIds}
            )

        states = self._session.scalars(
            select(models.InterventionMilestone.status).where(
                models.InterventionMilestone.interventionId == parent.id
            )
        ).all()
        derived = rules.derive_activity_status(list(states))
        current = enums.InterventionStatus(parent.status)
        if derived is not current and derived in rules.ALLOWED_TRANSITIONS[current]:
            parent.status = derived.value
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="interventions.milestone.completed",
            targetType="interventionMilestone",
            targetId=milestone.id,
            requestId=requestId,
        )
        return milestone

    def transition(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        interventionId: UUID,
        targetStatus: str | enums.InterventionStatus,
        rationale: str,
        verificationAssessmentRef: str | None = None,
        requestId: str | None = None,
    ) -> models.Intervention:
        """Apply the explicit transition table and recovery verification gate."""
        require_permission(principal, Permission.INTERVENTION_WRITE, organisationId)
        record = self._get_intervention(organisationId, interventionId)
        require_text(rationale, "rationale")
        targetValue = rules.require_enum(
            enums.InterventionStatus, targetStatus, "targetStatus"
        )
        rules.assert_transition(
            record.status,
            targetValue,
            verificationAssessmentRef=verificationAssessmentRef,
        )
        record.status = targetValue.value
        if targetValue is enums.InterventionStatus.RECOVERY_VERIFIED:
            try:
                record.verificationAssessmentId = UUID(verificationAssessmentRef or "")
            except ValueError as error:
                raise DomainError(
                    ErrorCode.NOT_FOUND,
                    "The verification assessment reference must be a valid UUID.",
                    statusCode=404,
                    field="verificationAssessmentRef",
                ) from error
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="interventions.intervention.transitioned",
            targetType="intervention",
            targetId=record.id,
            detail={"status": record.status, "rationale": rationale.strip()},
            requestId=requestId,
        )
        return record

    def _get_intervention(
        self, organisationId: UUID, interventionId: UUID
    ) -> models.Intervention:
        record = self._session.get(models.Intervention, interventionId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Intervention not found.",
                statusCode=404,
                field="interventionId",
            )
        return record
