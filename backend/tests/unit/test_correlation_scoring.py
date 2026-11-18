"""Scoring tests.

These cover the rules that fail silently in production: an absent signal must
stay absent, an unrelated pair must not look like an absent one, and a repost
must not read as a second witness.
"""

from datetime import UTC, datetime, timedelta

import pytest

from ecowatch.correlation.features import Location, ObservationFeatures
from ecowatch.correlation.scoring import (
    haversine_km,
    rank,
    score_pair,
    temporal_proximity,
    token_similarity,
)

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)


def obs(observation_id: str, **kwargs) -> ObservationFeatures:
    return ObservationFeatures(observation_id=observation_id, **kwargs)


def test_text_only_pair_scores_on_text_alone() -> None:
    a = obs("a", text="dead fish floating near the weir")
    b = obs("b", text="dead fish floating near the weir")

    suggestion = score_pair(a, b)

    assert suggestion is not None
    assert suggestion.components == {"semantic_similarity": 1.0}
    assert suggestion.score == pytest.approx(1.0)
    # Location, time and category were never recorded, so they are named as
    # absent rather than assumed.
    assert len(suggestion.missing_signals) == 3


def test_absent_signals_are_not_penalised() -> None:
    """A pair known on two signals scores on those two, unweighted by the rest."""
    a = obs("a", text="oil slick on the river", category="water")
    b = obs("b", text="oil slick on the river", category="water")

    suggestion = score_pair(a, b)

    assert suggestion is not None
    expected = (0.45 * 1.0 + 0.10 * 1.0) / (0.45 + 0.10)
    assert suggestion.score == pytest.approx(expected)
    assert set(suggestion.components) == {"semantic_similarity", "category_agreement"}


def test_no_comparable_signal_returns_nothing_rather_than_zero() -> None:
    """Zero would read as 'checked and unrelated'. We cannot say that."""
    assert score_pair(obs("a"), obs("b")) is None


def test_unrelated_text_scores_zero_and_is_not_missing() -> None:
    a = obs("a", text="dead fish")
    b = obs("b", text="illegal dumping")

    suggestion = score_pair(a, b)

    assert suggestion is not None
    assert suggestion.components["semantic_similarity"] == 0.0
    assert suggestion.score == pytest.approx(0.0)
    # The text is comparable and says "unlike". Time, place and category were
    # never recorded, so they are still named as absent.
    assert "no usable text to compare" not in suggestion.missing_signals
    assert len(suggestion.missing_signals) == 3


def test_times_beyond_the_window_score_zero_and_stay_present() -> None:
    a = obs("a", observed_at=T0)
    b = obs("b", observed_at=T0 + timedelta(hours=100))

    suggestion = score_pair(a, b, temporal_window_hours=72)

    assert suggestion is not None
    assert suggestion.components["temporal_proximity"] == 0.0
    assert "no observation time recorded" not in suggestion.missing_signals


def test_same_source_is_flagged_as_not_independent() -> None:
    a = obs("a", text="spill at the outfall", source_ref="post-1234")
    b = obs("b", text="spill at the outfall", source_ref="post-1234")

    suggestion = score_pair(a, b)

    assert suggestion is not None
    assert suggestion.source_independent is False
    assert any("not independent" in reason for reason in suggestion.reasons)


def test_different_sources_are_independent() -> None:
    a = obs("a", text="spill at the outfall", source_ref="post-1234")
    b = obs("b", text="spill at the outfall", source_ref="post-9999")

    suggestion = score_pair(a, b)

    assert suggestion is not None
    assert suggestion.source_independent is True


def test_suggestion_is_always_unverified() -> None:
    suggestion = score_pair(obs("a", text="dead fish"), obs("b", text="dead fish"))
    assert suggestion is not None
    assert suggestion.status == "unverified"


def test_naive_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        obs("a", observed_at=datetime(2026, 11, 1, 9, 0))


def test_out_of_range_coordinates_are_rejected() -> None:
    with pytest.raises(ValueError, match="latitude"):
        Location(lat=91.0, lon=0.0)


def test_pairing_an_observation_with_itself_is_rejected() -> None:
    a = obs("a", text="x")
    with pytest.raises(ValueError, match="two different observations"):
        score_pair(a, a)


def test_temporal_proximity_uses_the_window() -> None:
    assert temporal_proximity(T0, T0, 72) == pytest.approx(1.0)
    assert temporal_proximity(T0, T0 + timedelta(hours=36), 72) == pytest.approx(0.5)
    assert temporal_proximity(T0, None, 72) is None


def test_haversine_is_close_to_a_known_distance() -> None:
    # One degree of longitude at the equator is about 111.2 km.
    assert haversine_km(0.0, 0.0, 0.0, 1.0) == pytest.approx(111.19, abs=0.05)


def test_spatial_proximity_scales_with_the_radius() -> None:
    a = obs("a", location=Location(lat=0.0, lon=0.0))
    b = obs("b", location=Location(lat=0.0, lon=1.0))

    near = score_pair(a, b, radius_km=200.0)
    far = score_pair(a, b, radius_km=25.0)

    assert near is not None and far is not None
    assert near.components["spatial_proximity"] == pytest.approx(1 - 111.19 / 200, abs=0.001)
    assert far.components["spatial_proximity"] == 0.0


def test_token_similarity_ignores_stopwords_and_empty_text() -> None:
    assert token_similarity("", "dead fish") is None
    assert token_similarity("the and for", "dead fish") is None
    assert token_similarity("dead fish", "dead fish") == pytest.approx(1.0)


def test_rank_orders_by_score_and_flags_a_close_top_two() -> None:
    subject = obs("s", text="chemical spill at the weir")
    close = obs("close", text="chemical spill at the weir")
    distant = obs("distant", text="noise complaint about traffic")

    ranking = rank(subject, [distant, close])

    assert [s.observation_b_id for s in ranking.suggestions] == ["close", "distant"]
    # closeness and distance differ far more than the default margin
    assert ranking.ambiguous_at_top is False


def test_rank_flags_ambiguity_when_the_top_two_cannot_be_separated() -> None:
    subject = obs("s", text="chemical spill at the weir")
    first = obs("first", text="chemical spill at the weir")
    second = obs("second", text="chemical spill at the weir")

    ranking = rank(subject, [first, second])

    assert ranking.ambiguous_at_top is True


def test_rank_skips_candidates_with_nothing_to_compare() -> None:
    subject = obs("s", text="chemical spill at the weir")

    ranking = rank(subject, [obs("blank")])

    assert ranking.suggestions == ()
    assert ranking.top is None
    assert ranking.ambiguous_at_top is False
