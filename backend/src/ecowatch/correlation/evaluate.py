"""Precision/recall for correlation suggestions against human labels.

This is the Phase 2 evaluation harness (`tests/evaluation/` in the plan). It is
a pure function over in-memory pairs so it can run against a consented or
synthetic labelled set without putting seed data in the product database
(`DR-018`, `docs/AGENT_GUIDE.md` section 5).

A suggestion carries no accuracy claim on its own. Only a scored run on real
reviewed decisions justifies a number, and even then the number describes the
harness, not the world.

`shortcut: reviews are supplied as labels; reviewer override rate is not
computed here because it needs real reviewer decisions, which do not exist
until the review UI ships.`
"""

from __future__ import annotations

from dataclasses import dataclass

from .features import PairSuggestion


@dataclass(frozen=True, slots=True)
class Label:
    """A human decision that two observations are, or are not, the same event."""

    observation_a_id: str
    observation_b_id: str
    same_event: bool

    @property
    def pair_key(self) -> tuple[str, str]:
        first, second = sorted((self.observation_a_id, self.observation_b_id))
        return (first, second)


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Counts and ratios. `None` where a ratio has no denominator.

    `unlabelled` counts suggestions with no human label. They are not counted
    as mistakes, and they are not counted as successes: reporting them
    separately is the only honest option.
    """

    threshold: float
    true_positives: int
    false_positives: int
    false_negatives: int
    unlabelled: int

    @property
    def precision(self) -> float | None:
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator else None

    @property
    def recall(self) -> float | None:
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator else None


def evaluate(
    suggestions: list[PairSuggestion], labels: list[Label], *, threshold: float = 0.5
) -> Evaluation:
    """Compare suggestions against labels at `threshold`.

    A pair offered twice (in both directions) is counted once, because scoring
    is symmetric and pair_key canonicalises the ordering.
    """
    truth = {label.pair_key: label.same_event for label in labels}
    offered: set[tuple[str, str]] = set()
    predicted: set[tuple[str, str]] = set()
    true_positives = false_positives = unlabelled = 0

    for suggestion in suggestions:
        key = suggestion.pair_key
        if key in offered:
            continue
        offered.add(key)
        if suggestion.score < threshold:
            continue
        predicted.add(key)
        if key not in truth:
            unlabelled += 1
        elif truth[key]:
            true_positives += 1
        else:
            false_positives += 1

    false_negatives = sum(1 for key, same_event in truth.items() if same_event and key not in predicted)

    return Evaluation(threshold, true_positives, false_positives, false_negatives, unlabelled)
