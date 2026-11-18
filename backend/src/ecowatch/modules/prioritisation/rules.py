"""Domain rules preventing imputed or severity-like prioritisation output."""

from __future__ import annotations

from typing import Any

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.prioritisation import enums

FACTOR_KEYS: tuple[str, ...] = (
    "magnitude",
    "extent",
    "persistence",
    "ecosystemSensitivity",
    "communityExposure",
    "evidenceQuality",
    "reversibility",
    "urgency",
    "connectivity",
    "dataGaps",
    "responseFeasibility",
    "responseAuthority",
)


def is_present_factor(value: object) -> bool:
    """Return True only when a factor carries an explicit, non-empty value."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def build_factor_view(factors: dict[str, Any]) -> dict[str, object]:
    """Split factors into present and missing without filling any gaps."""
    unknown = sorted(set(factors) - set(FACTOR_KEYS))
    if unknown:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"Unsupported prioritisation factor: {unknown[0]}.",
            field=f"factors.{unknown[0]}",
        )
    values = {key: value for key, value in factors.items() if is_present_factor(value)}
    present = [key for key in FACTOR_KEYS if key in values]
    missing = [key for key in FACTOR_KEYS if key not in values]
    return {"present": present, "missing": missing, "values": values}


def assert_assessment_honest(
    *,
    factors: dict[str, Any],
    compositeRank: float | None,
    rankingMethodRef: str | None,
    rankIsNotSeverity: bool | None,
    decision: str | enums.PriorityDecision | None,
    rationale: str | None,
    decidedByUserId: object | None,
) -> dict[str, object]:
    """Refuse unexplained ranks and require human accountability for decisions."""
    factorView = build_factor_view(factors)
    if not factorView["present"]:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "At least one prioritisation factor must be recorded.",
            field="factors",
        )

    if compositeRank is not None:
        if rankingMethodRef is None or not rankingMethodRef.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A composite rank requires a documented ranking method.",
                field="rankingMethodRef",
            )
        if rankIsNotSeverity is not True:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A composite rank must be explicitly recorded as not a severity judgement.",
                field="rankIsNotSeverity",
            )

    if decision is not None:
        try:
            enums.PriorityDecision(decision)
        except ValueError as error:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Unsupported priority decision.",
                field="decision",
            ) from error
        if decidedByUserId is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A priority decision requires a deciding user.",
                field="decidedByUserId",
            )
        if rationale is None or not rationale.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A priority decision requires a rationale.",
                field="rationale",
            )

    return factorView
