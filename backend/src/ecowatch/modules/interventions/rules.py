"""Domain rules for intervention transitions and evidence-level ordering."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.interventions import enums

ALLOWED_TRANSITIONS: dict[enums.InterventionStatus, frozenset[enums.InterventionStatus]] = {
    enums.InterventionStatus.PROPOSED: frozenset(
        {enums.InterventionStatus.APPROVED, enums.InterventionStatus.CANCELLED}
    ),
    enums.InterventionStatus.APPROVED: frozenset(
        {enums.InterventionStatus.SCHEDULED, enums.InterventionStatus.CANCELLED}
    ),
    enums.InterventionStatus.SCHEDULED: frozenset(
        {enums.InterventionStatus.IN_PROGRESS, enums.InterventionStatus.CANCELLED}
    ),
    enums.InterventionStatus.IN_PROGRESS: frozenset(
        {enums.InterventionStatus.ACTIVITY_COMPLETED, enums.InterventionStatus.CANCELLED}
    ),
    enums.InterventionStatus.ACTIVITY_COMPLETED: frozenset(
        {enums.InterventionStatus.OUTCOME_MONITORING, enums.InterventionStatus.CANCELLED}
    ),
    enums.InterventionStatus.OUTCOME_MONITORING: frozenset(
        {
            enums.InterventionStatus.IMPROVEMENT_OBSERVED,
            enums.InterventionStatus.NO_IMPROVEMENT,
            enums.InterventionStatus.DETERIORATION,
            enums.InterventionStatus.INCONCLUSIVE,
            enums.InterventionStatus.RECOVERY_VERIFIED,
            enums.InterventionStatus.CANCELLED,
        }
    ),
    enums.InterventionStatus.IMPROVEMENT_OBSERVED: frozenset(
        {
            enums.InterventionStatus.OUTCOME_MONITORING,
            enums.InterventionStatus.RECOVERY_VERIFIED,
            enums.InterventionStatus.INCONCLUSIVE,
        }
    ),
    enums.InterventionStatus.NO_IMPROVEMENT: frozenset(
        {enums.InterventionStatus.OUTCOME_MONITORING, enums.InterventionStatus.INCONCLUSIVE}
    ),
    enums.InterventionStatus.DETERIORATION: frozenset(
        {enums.InterventionStatus.OUTCOME_MONITORING, enums.InterventionStatus.INCONCLUSIVE}
    ),
    enums.InterventionStatus.INCONCLUSIVE: frozenset(
        {enums.InterventionStatus.OUTCOME_MONITORING}
    ),
    enums.InterventionStatus.RECOVERY_VERIFIED: frozenset(),
    enums.InterventionStatus.CANCELLED: frozenset(),
}


def require_enum(
    enumClass: type[StrEnum],
    value: str | StrEnum | None,
    fieldName: str,
) -> StrEnum:
    """Resolve a value against an enumeration or raise a field-level error."""
    if value is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, f"{fieldName} is required.", field=fieldName
        )
    try:
        return enumClass(value)
    except ValueError as error:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"{fieldName} has an unsupported value.",
            field=fieldName,
        ) from error


def assert_transition(
    current: str | enums.InterventionStatus,
    target: str | enums.InterventionStatus,
    *,
    verificationAssessmentRef: str | None = None,
) -> None:
    """Enforce the explicit intervention transition table and recovery gate."""
    currentValue = require_enum(enums.InterventionStatus, current, "current")
    targetValue = require_enum(enums.InterventionStatus, target, "target")
    if targetValue not in ALLOWED_TRANSITIONS[currentValue]:
        raise DomainError(
            ErrorCode.INVALID_STATUS_TRANSITION,
            f"Illegal intervention transition: {currentValue.value} -> {targetValue.value}.",
            field="status",
        )
    if targetValue is enums.InterventionStatus.RECOVERY_VERIFIED and (
        verificationAssessmentRef is None or not verificationAssessmentRef.strip()
    ):
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "Recovery cannot be marked from activity completion; "
            "an approved verification assessment is required.",
            field="verificationAssessmentRef",
        )


def derive_activity_status(
    milestoneStates: list[str | enums.MilestoneStatus],
) -> enums.InterventionStatus:
    """Derive only activity status from milestones, never an environmental outcome."""
    if not milestoneStates:
        return enums.InterventionStatus.SCHEDULED
    states = [
        require_enum(enums.MilestoneStatus, item, "milestoneStatus")
        for item in milestoneStates
    ]
    active = [item for item in states if item is not enums.MilestoneStatus.CANCELLED]
    if not active:
        return enums.InterventionStatus.CANCELLED
    if all(item is enums.MilestoneStatus.COMPLETED for item in active):
        return enums.InterventionStatus.ACTIVITY_COMPLETED
    if any(
        item in (enums.MilestoneStatus.IN_PROGRESS, enums.MilestoneStatus.COMPLETED)
        for item in active
    ):
        return enums.InterventionStatus.IN_PROGRESS
    return enums.InterventionStatus.SCHEDULED


def assert_intervention_basics(
    *,
    objective: str | None,
    responsibleOrganisationId: object | None,
    authorisedLeadUserId: object | None,
    plannedStartAt: datetime | None,
    plannedEndAt: datetime | None,
) -> None:
    """Require ownership and a coherent planned window for an intervention."""
    if objective is None or not objective.strip():
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "objective is required for an intervention.",
            field="objective",
        )
    if responsibleOrganisationId is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "responsibleOrganisationId is required.",
            field="responsibleOrganisationId",
        )
    if authorisedLeadUserId is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "authorisedLeadUserId is required.",
            field="authorisedLeadUserId",
        )
    if (
        plannedStartAt is not None
        and plannedEndAt is not None
        and plannedStartAt > plannedEndAt
    ):
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "plannedStartAt must not be after plannedEndAt.",
            field="plannedEndAt",
        )


def assert_evidence_level_ordering(
    *,
    activityCompleted: bool,
    outputDelivered: bool,
    environmentalOutcome: bool,
    recoveryVerified: bool,
) -> None:
    """Keep activity, output, outcome, and recovery strictly ordered."""
    if outputDelivered and not activityCompleted:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Output cannot be delivered before activity completion.",
            field="activityCompleted",
        )
    if environmentalOutcome and not outputDelivered:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "An environmental outcome cannot be recorded before an output is delivered.",
            field="outputDelivered",
        )
    if recoveryVerified and not environmentalOutcome:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Recovery cannot be verified before an environmental outcome is recorded.",
            field="environmentalOutcome",
        )
