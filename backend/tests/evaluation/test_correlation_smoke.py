"""Smoke-test the correlation harness on temporary, synthetic fixtures.

The counts asserted here prove the scoring-to-evaluation wiring only. They are
not a measurement of EcoWatch accuracy and must never be reported as one
(`ADR-030`, owner decision 2026-11-18).
"""

from datetime import UTC, datetime, timedelta

import pytest

from ecowatch.modules.correlation.evaluate import Label, evaluate
from ecowatch.modules.correlation.features import Location, ObservationFeatures
from ecowatch.modules.correlation.scoring import score_pair


def test_scored_pairs_feed_the_harness_without_an_accuracy_claim() -> None:
    base = datetime(2026, 11, 18, 12, tzinfo=UTC)
    reports = [
        ObservationFeatures(
            "a",
            text="oily sheen at the river bend",
            observed_at=base,
            location=Location(6.5, -1.5),
            category="water_pollution",
        ),
        ObservationFeatures(
            "b",
            text="oily sheen at the river bend",
            observed_at=base + timedelta(minutes=10),
            location=Location(6.5001, -1.5001),
            category="water_pollution",
        ),
        ObservationFeatures(
            "c",
            text="market stall fire on the high street",
            observed_at=base + timedelta(minutes=20),
            location=Location(6.5002, -1.5002),
            category="water_pollution",
        ),
        ObservationFeatures(
            "d",
            text="unrelated night noise",
            observed_at=base + timedelta(hours=200),
            location=Location(20.0, 20.0),
            category="noise",
        ),
    ]

    suggestions = []
    for index, first in enumerate(reports):
        for second in reports[index + 1 :]:
            suggestion = score_pair(first, second)
            if suggestion is not None:
                suggestions.append(suggestion)

    labels = [
        Label("a", "b", True),
        Label("a", "c", False),
        Label("a", "d", True),
    ]
    result = evaluate(suggestions, labels, threshold=0.5)

    assert (result.true_positives, result.false_positives, result.false_negatives) == (1, 1, 1)
    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)
    # A pair with no human label is counted, never quietly treated as correct.
    assert result.unlabelled == 1
