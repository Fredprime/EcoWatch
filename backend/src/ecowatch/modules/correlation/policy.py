"""How far to look for related reports, per category.

Two bounds exist because a candidate needs both: a distance and a time window.
A candidate outside either is not a candidate, so the bounds live here rather
than being duplicated at the call site and in the scoring defaults.

Categories are free text in this product (Phase 1 stores `observation_type` as a
string, docs/PHASE2_TODO.md), so this is a small explicit table of the categories
the product actually uses plus a default. An unknown string gets the default --
an unrecognised label is not evidence that a report is unusual.

`shortcut: exact normalised string match, no prefix or synonym handling. Being
wrong here costs recall, never correctness: a miss only means a wider default
window is used. Revisit if Phase 1 ever ships a category vocabulary.`
"""

from __future__ import annotations

from dataclasses import dataclass

from .scoring import DEFAULT_RADIUS_KM, DEFAULT_TEMPORAL_WINDOW_HOURS

# When a subject has no location, distance bounds nothing, so the window is the
# only remaining limit on the candidate set -- and the LIMIT is shared with
# every report in the organisation. Left wide, far-away reports crowd out the
# plausible ones. So it tightens rather than staying open.
WITHOUT_LOCATION_WINDOW_FACTOR = 0.25


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    """Distance and time bounds for one scan."""

    radius_km: float
    window_hours: float

    def without_location(self) -> RetrievalPolicy:
        """Tighter time window, for a report that carries no point."""
        return RetrievalPolicy(
            radius_km=self.radius_km,
            window_hours=self.window_hours * WITHOUT_LOCATION_WINDOW_FACTOR,
        )


DEFAULT_POLICY = RetrievalPolicy(
    radius_km=DEFAULT_RADIUS_KM, window_hours=DEFAULT_TEMPORAL_WINDOW_HOURS
)

# Reasons for the numbers, so the next person can argue with the value instead
# of guessing where it came from:
#   air    disperses far and changes fast
#   noise  short range, short memory
#   waste  dumped material stays put for a long time
#   water  flows; wider than a noise complaint, shorter-lived than a dump
POLICY_BY_CATEGORY: dict[str, RetrievalPolicy] = {
    "air_pollution": RetrievalPolicy(radius_km=50.0, window_hours=24.0),
    "noise": RetrievalPolicy(radius_km=5.0, window_hours=12.0),
    "waste": RetrievalPolicy(radius_km=15.0, window_hours=168.0),
    "water_pollution": RetrievalPolicy(radius_km=25.0, window_hours=72.0),
}


def policy_for(category: str | None, *, has_location: bool) -> RetrievalPolicy:
    """Bounds for a scan. Unknown or absent category gets the default."""
    policy = POLICY_BY_CATEGORY.get(category.strip().lower()) if category else None
    policy = policy or DEFAULT_POLICY
    return policy if has_location else policy.without_location()
