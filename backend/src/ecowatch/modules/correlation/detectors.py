"""Which detector a pair belongs to, and the threshold that decides it.

One task per pair, most specific first. A repost that also happens to use
identical wording is one fact about the pair, not two: writing both a
`source_dependency` row and a `duplicate` row for it would put the same pair in
the reviewer's queue twice and make the queue look bigger than it is.

Tasks that are not decided here:

  `cross_case`      needs the case-side rules (`docs/PERMISSIONS_MATRIX.md` section 4)
                    and the cases module, which Phase 1 owns.
  `merge`/`split`   case actions, not detectors.

Thresholds are queue-tuning knobs, not correctness boundaries. `same_event` is
deliberately low: a false suggestion costs a reviewer two seconds to reject,
while a missed link is invisible. That trade can only be judged once the
evaluation run exists (plan section 6 item 5).
"""

from __future__ import annotations

from ecowatch.modules.correlation.features import PairSuggestion
from ecowatch.modules.correlation.models import CorrelationTask

# Nearly the same distinctive words: usually one report submitted twice.
DUPLICATE_TEXT_THRESHOLD = 0.9
# Anything below this is not worth a reviewer's attention at all.
SAME_EVENT_THRESHOLD = 0.45

TASK_REASONS: dict[CorrelationTask, str] = {
    CorrelationTask.SOURCE_DEPENDENCY: (
        "the two reports share an original source, so they are one account, not two"
    ),
    CorrelationTask.DUPLICATE: (
        "the two reports use nearly the same words, which is usually the same "
        "report submitted twice"
    ),
    CorrelationTask.SAME_EVENT: (
        "the reports may describe the same occurrence; a reviewer decides whether "
        "they do"
    ),
}


def task_for(suggestion: PairSuggestion) -> CorrelationTask | None:
    """The most specific task this pair qualifies for, or None below threshold."""
    if not suggestion.source_independent:
        return CorrelationTask.SOURCE_DEPENDENCY
    if suggestion.components.get("semantic_similarity", 0.0) >= DUPLICATE_TEXT_THRESHOLD:
        return CorrelationTask.DUPLICATE
    if suggestion.score >= SAME_EVENT_THRESHOLD:
        return CorrelationTask.SAME_EVENT
    return None
