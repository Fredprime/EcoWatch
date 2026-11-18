"""Canonical enumerations for prioritisation."""

from enum import StrEnum


class PriorityDecision(StrEnum):
    """Human decision recorded after considering prioritisation factors."""

    PRIORITY_SET = "priority_set"
    DEFERRED = "deferred"
    NO_ACTION = "no_action"


class PriorityBand(StrEnum):
    """Optional descriptive band; never a severity or probability."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
