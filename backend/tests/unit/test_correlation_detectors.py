"""Detector selection: one task per pair, most specific first."""

from ecowatch.modules.correlation.detectors import (
    DUPLICATE_TEXT_THRESHOLD,
    SAME_EVENT_THRESHOLD,
    TASK_REASONS,
    task_for,
)
from ecowatch.modules.correlation.features import PairSuggestion
from ecowatch.modules.correlation.models import CorrelationTask


def suggestion(
    *, score: float, components: dict[str, float], source_independent: bool = True
) -> PairSuggestion:
    return PairSuggestion(
        observation_a_id="a",
        observation_b_id="b",
        score=score,
        components=components,
        missing_signals=(),
        reasons=(),
        source_independent=source_independent,
    )


def test_shared_source_wins_over_everything_else() -> None:
    """A repost with identical wording is one fact, not two rows in the queue."""
    pair = suggestion(
        score=0.99, components={"semantic_similarity": 1.0}, source_independent=False
    )
    assert task_for(pair) == CorrelationTask.SOURCE_DEPENDENCY


def test_identical_wording_is_a_duplicate_not_a_same_event() -> None:
    pair = suggestion(score=0.95, components={"semantic_similarity": 1.0})
    assert task_for(pair) == CorrelationTask.DUPLICATE


def test_moderate_overlap_is_a_same_event() -> None:
    pair = suggestion(score=0.6, components={"semantic_similarity": 0.5})
    assert task_for(pair) == CorrelationTask.SAME_EVENT


def test_below_threshold_is_not_suggested_at_all() -> None:
    """Otherwise every report in the organisation becomes a suggestion."""
    pair = suggestion(score=SAME_EVENT_THRESHOLD - 0.01, components={"semantic_similarity": 0.1})
    assert task_for(pair) is None


def test_threshold_boundaries_are_inclusive_and_named() -> None:
    atDuplicate = suggestion(
        score=0.95, components={"semantic_similarity": DUPLICATE_TEXT_THRESHOLD}
    )
    assert task_for(atDuplicate) == CorrelationTask.DUPLICATE
    atSameEvent = suggestion(score=SAME_EVENT_THRESHOLD, components={"semantic_similarity": 0.1})
    assert task_for(atSameEvent) == CorrelationTask.SAME_EVENT
    # Every task the detector can return has wording a reviewer can read.
    assert set(TASK_REASONS) == {
        CorrelationTask.SOURCE_DEPENDENCY,
        CorrelationTask.DUPLICATE,
        CorrelationTask.SAME_EVENT,
    }
