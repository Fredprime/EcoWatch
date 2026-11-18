"""Evidence Correlation and Incident Intelligence (Phase 2).

Produces pairwise suggestions for a human reviewer. Nothing in this module
decides that two reports are the same event, that a source is responsible, or
that harm occurred.
"""

from ecowatch.modules.correlation.evaluate import Evaluation, Label, evaluate
from ecowatch.modules.correlation.features import (
    Location,
    ObservationFeatures,
    PairSuggestion,
    Ranking,
)
from ecowatch.modules.correlation.scoring import rank, score_pair

__all__ = [
    "Evaluation",
    "Label",
    "Location",
    "ObservationFeatures",
    "PairSuggestion",
    "Ranking",
    "evaluate",
    "rank",
    "score_pair",
]
