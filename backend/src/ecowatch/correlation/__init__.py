"""Evidence Correlation engine (Phase 2).

Produces pairwise suggestions for a human reviewer. Nothing here decides that
two reports are the same event, that a source is responsible, or that harm
occurred.
"""

from .evaluate import Evaluation, Label, evaluate
from .features import Location, ObservationFeatures, PairSuggestion, Ranking
from .scoring import rank, score_pair

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
