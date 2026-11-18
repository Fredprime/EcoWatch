"""Canonical enumerations for interventions and milestones."""

from enum import StrEnum


class InterventionStatus(StrEnum):
    """Intervention lifecycle statuses; activity and outcome are never conflated."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    ACTIVITY_COMPLETED = "activity_completed"
    OUTCOME_MONITORING = "outcome_monitoring"
    IMPROVEMENT_OBSERVED = "improvement_observed"
    NO_IMPROVEMENT = "no_improvement"
    DETERIORATION = "deterioration"
    INCONCLUSIVE = "inconclusive"
    RECOVERY_VERIFIED = "recovery_verified"
    CANCELLED = "cancelled"


class MilestoneStatus(StrEnum):
    """Delivery status of an intervention milestone."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EvidenceLevel(StrEnum):
    """Ordered evidence levels from activity completion to recovery verification."""

    ACTIVITY_COMPLETED = "activity_completed"
    OUTPUT_DELIVERED = "output_delivered"
    ENVIRONMENTAL_OUTCOME = "environmental_outcome"
    RECOVERY_VERIFIED = "recovery_verified"
