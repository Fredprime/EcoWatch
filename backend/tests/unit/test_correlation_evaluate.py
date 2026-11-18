"""Evaluation harness tests.

The harness exists so Phase 2 has an acceptance gate that does not depend on
seed data in the product database. These tests fix its counting rules, because
a harness that counts generously is worse than no harness.
"""

import pytest

from ecowatch.correlation.evaluate import Label, evaluate
from ecowatch.correlation.features import PairSuggestion


def suggestion(a: str, b: str, score: float) -> PairSuggestion:
    return PairSuggestion(a, b, score, {}, (), (), True)


def test_counts_true_positive_false_positive_and_missed_link() -> None:
    suggestions = [suggestion("a", "b", 0.9), suggestion("a", "c", 0.8)]
    labels = [
        Label("a", "b", True),
        Label("a", "c", False),
        Label("b", "c", True),  # never offered, so it is a missed link
    ]

    result = evaluate(suggestions, labels, threshold=0.5)

    assert (result.true_positives, result.false_positives, result.false_negatives) == (1, 1, 1)
    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)


def test_below_threshold_suggestion_is_not_a_prediction() -> None:
    suggestions = [suggestion("a", "b", 0.2)]
    labels = [Label("a", "b", True)]

    result = evaluate(suggestions, labels, threshold=0.5)

    assert result.true_positives == 0
    assert result.false_negatives == 1


def test_the_same_pair_offered_in_both_directions_counts_once() -> None:
    suggestions = [suggestion("a", "b", 0.9), suggestion("b", "a", 0.9)]
    labels = [Label("a", "b", True)]

    result = evaluate(suggestions, labels, threshold=0.5)

    assert result.true_positives == 1
    assert result.false_positives == 0


def test_unlabelled_suggestions_are_reported_separately() -> None:
    suggestions = [suggestion("a", "b", 0.9)]
    labels: list[Label] = []

    result = evaluate(suggestions, labels, threshold=0.5)

    assert result.unlabelled == 1
    assert result.true_positives == 0
    assert result.false_positives == 0
    # No labels at all means no ratio can be claimed.
    assert result.precision is None
    assert result.recall is None


def test_labels_are_direction_independent() -> None:
    suggestions = [suggestion("b", "a", 0.9)]
    labels = [Label("a", "b", True)]

    result = evaluate(suggestions, labels, threshold=0.5)

    assert result.true_positives == 1
