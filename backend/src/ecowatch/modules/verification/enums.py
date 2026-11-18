"""Canonical enumerations for indicator verification and publication."""

from enum import StrEnum


class MeasurementQualifier(StrEnum):
    """Qualifier describing how a measurement value relates to a detection limit."""

    EXACT = "exact"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"
    NOT_DETECTED = "not_detected"


class ExpectedDirection(StrEnum):
    """Expected direction of environmental change for an indicator."""

    INCREASE = "increase"
    DECREASE = "decrease"
    EITHER = "either"


class OutcomeConclusion(StrEnum):
    """Observed-change conclusion; recovery requires a separate gated assessment."""

    IMPROVEMENT = "improvement"
    NO_IMPROVEMENT = "no_improvement"
    DETERIORATION = "deterioration"
    INCONCLUSIVE = "inconclusive"
    RECOVERY_VERIFIED = "recovery_verified"


class AssessmentStatus(StrEnum):
    """Lifecycle status of a verification assessment."""

    DRAFT = "draft"
    FINAL = "final"
    RETRACTED = "retracted"
