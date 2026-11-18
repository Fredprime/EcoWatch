"""Inputs and outputs of the Evidence Correlation engine.

Phase 2, module `correlation`. Standard library only, no database access:
scoring must be testable without a database and must never be able to reach
contributor identity.

Integrity rules encoded here (docs/AGENT_GUIDE.md section 5, ADR-006):
  - A score is a ranking signal for a human reviewer. It is not a probability,
    not a severity, not a danger level, and not a conclusion.
  - A signal that is absent is reported as absent. It is never imputed.
  - A suggestion is always `unverified`. Nothing in this package may promote it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# A suggestion can only ever carry this status. Annotated as a Literal so that
# assigning anything else is a type error and a runtime-visible mistake.
SUGGESTION_STATUS: Literal["unverified"] = "unverified"


@dataclass(frozen=True, slots=True)
class Location:
    """A reported point. Coordinates are the contributor's, not a corrected copy."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"latitude out of range: {self.lat}")
        if not -180.0 <= self.lon <= 180.0:
            raise ValueError(f"longitude out of range: {self.lon}")


@dataclass(frozen=True, slots=True)
class ObservationFeatures:
    """The minimum of an observation that correlation is allowed to compare.

    Every field except `observation_id` is optional, because the product
    permits a report with no location, no time, or no text. An absent field
    must stay absent rather than be filled with a default.
    """

    observation_id: str
    text: str | None = None
    observed_at: datetime | None = None
    location: Location | None = None
    category: str | None = None
    source_ref: str | None = None
    embedding: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required")
        if self.observed_at is not None and self.observed_at.tzinfo is None:
            # A naive time would be silently compared against a UTC time and
            # produce a wrong number of hours. Refuse it instead.
            raise ValueError(
                f"{self.observation_id}: observed_at must be timezone-aware; "
                "a naive datetime is ambiguous, not midnight"
            )


@dataclass(frozen=True, slots=True)
class PairSuggestion:
    """One 'these two might be related' result, with its reasons.

    `components` holds only signals that were available. `missing_signals`
    names the ones that were not, so a reviewer can see what the score could
    not see.
    """

    observation_a_id: str
    observation_b_id: str
    score: float
    components: dict[str, float]
    missing_signals: tuple[str, ...]
    reasons: tuple[str, ...]
    source_independent: bool
    status: Literal["unverified"] = SUGGESTION_STATUS

    @property
    def pair_key(self) -> tuple[str, str]:
        """Canonical ordering, so (a, b) and (b, a) collapse to one pair."""
        first, second = sorted((self.observation_a_id, self.observation_b_id))
        return (first, second)


@dataclass(frozen=True, slots=True)
class Ranking:
    """Suggestions for one observation, best first.

    `ambiguous_at_top` is set when the top two are too close to separate. The
    caller must surface that as a tie for a human, never break it silently.
    """

    for_observation_id: str
    suggestions: tuple[PairSuggestion, ...]
    ambiguous_at_top: bool

    @property
    def top(self) -> PairSuggestion | None:
        return self.suggestions[0] if self.suggestions else None
