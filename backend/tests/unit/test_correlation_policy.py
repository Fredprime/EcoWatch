"""Retrieval policy: the bounds a scan uses, and what happens without a location."""

from ecowatch.modules.correlation.policy import (
    DEFAULT_POLICY,
    POLICY_BY_CATEGORY,
    RetrievalPolicy,
    policy_for,
)
from ecowatch.modules.correlation.scoring import (
    DEFAULT_RADIUS_KM,
    DEFAULT_TEMPORAL_WINDOW_HOURS,
)


def test_known_category_uses_its_own_bounds() -> None:
    assert policy_for("noise", has_location=True) == POLICY_BY_CATEGORY["noise"]
    assert policy_for("noise", has_location=True).radius_km == 5.0


def test_category_matching_is_normalised_but_not_guessed() -> None:
    assert policy_for("  Noise  ", has_location=True) == POLICY_BY_CATEGORY["noise"]
    # An unknown label is not evidence of anything unusual: default bounds.
    assert policy_for("something_new", has_location=True) == DEFAULT_POLICY
    assert policy_for("noise_event", has_location=True) == DEFAULT_POLICY
    assert policy_for(None, has_location=True) == DEFAULT_POLICY
    assert policy_for("", has_location=True) == DEFAULT_POLICY


def test_missing_location_tightens_the_window_and_leaves_radius_alone() -> None:
    """With no point, only time bounds the candidate set, so time takes over."""
    located = policy_for("water_pollution", has_location=True)
    unlocated = policy_for("water_pollution", has_location=False)

    assert unlocated.radius_km == located.radius_km
    assert unlocated.window_hours < located.window_hours


def test_default_policy_matches_the_engine_defaults() -> None:
    """If these drift apart, retrieval and scoring disagree about the same scan."""
    assert RetrievalPolicy(
        radius_km=DEFAULT_RADIUS_KM, window_hours=DEFAULT_TEMPORAL_WINDOW_HOURS
    ) == DEFAULT_POLICY
