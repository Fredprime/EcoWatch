"""Pairwise scoring for the Evidence Correlation engine.

Four signals, each either a number in [0, 1] or absent:

    semantic_similarity  pgvector-backed text vectors when both exist, else
                         shared distinctive words in the two texts
    temporal_proximity    how close the two `observed_at` values are
    spatial_proximity     how close the two reported points are
    category_agreement    whether the two reports use the same category

The combined figure is a weighted mean over the signals that exist. A missing
signal is dropped from numerator *and* denominator, so a pair with only two
known signals is scored on those two rather than penalised for the others or
given a made-up value. If no signal exists at all, there is no suggestion --
not a zero, because zero would read as "checked and unrelated".

The result is an ordering aid for a reviewer. It is not a probability and must
never be rendered as one (`docs/13` section 3, `docs/AGENT_GUIDE.md` section 5).
"""

from __future__ import annotations

import math
import re
from datetime import datetime

from .features import ObservationFeatures, PairSuggestion, Ranking

WEIGHTS: dict[str, float] = {
    "semantic_similarity": 0.45,
    "temporal_proximity": 0.25,
    "spatial_proximity": 0.20,
    "category_agreement": 0.10,
}

# Absent signals are reported with these labels. Kept as plain words because
# they reach the reviewer's screen.
MISSING_LABELS: dict[str, str] = {
    "semantic_similarity": "no usable text to compare",
    "temporal_proximity": "no observation time recorded",
    "spatial_proximity": "no location recorded",
    "category_agreement": "no category recorded",
}

DEFAULT_TEMPORAL_WINDOW_HOURS = 72.0
DEFAULT_RADIUS_KM = 25.0

_WORD = re.compile(r"[a-z0-9']+")
_STOPWORDS_TEXT = (
    "the and for was were are been being with that this these those from have has had "
    "not but you your they them there here what when where which who whom how all any "
    "can could would should will shall may might must its into out over under again "
    "further then once about above below between during before after"
)
_STOPWORDS = frozenset(_STOPWORDS_TEXT.split())


def token_similarity(text_a: str | None, text_b: str | None) -> float | None:
    """Jaccard overlap of distinctive words, or None when there is nothing to compare.

    `shortcut: exact word overlap. Used only when one or both observations have
    no stored vector; the model itself remains an open decision (ADR-019).`

    Empty text is *absent*, not dissimilar: a report with no description must
    not be labelled as unlike every other report.
    """
    tokens_a = tokens(text_a)
    tokens_b = tokens(text_b)
    if not tokens_a or not tokens_b:
        return None
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def tokens(text: str | None) -> frozenset[str]:
    if not text:
        return frozenset()
    return frozenset(w for w in _WORD.findall(text.lower()) if len(w) > 2 and w not in _STOPWORDS)


def vector_similarity(
    first: tuple[float, ...] | list[float] | None,
    second: tuple[float, ...] | list[float] | None,
) -> float | None:
    """Cosine overlap, clamped to [0, 1], or None when no vectors exist."""
    if first is None or second is None or not first or not second:
        return None
    if len(first) != len(second):
        return None
    dot = math.fsum(left * right for left, right in zip(first, second, strict=True))
    firstNorm = math.sqrt(math.fsum(value * value for value in first))
    secondNorm = math.sqrt(math.fsum(value * value for value in second))
    if firstNorm == 0.0 or secondNorm == 0.0:
        return None
    return max(0.0, min(1.0, dot / (firstNorm * secondNorm)))


def semantic_similarity(first: ObservationFeatures, second: ObservationFeatures) -> float | None:
    """Use stored vectors when both exist, otherwise the labelled keyword fallback."""
    vectorScore = vector_similarity(first.embedding, second.embedding)
    return token_similarity(first.text, second.text) if vectorScore is None else vectorScore


def haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Great-circle distance in kilometres."""
    radius = 6371.0088
    phi_a, phi_b = math.radians(lat_a), math.radians(lat_b)
    d_phi = phi_b - phi_a
    d_lambda = math.radians(lon_b - lon_a)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi_a) * math.cos(phi_b) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def temporal_proximity(
    first: datetime | None,
    second: datetime | None,
    window_hours: float = DEFAULT_TEMPORAL_WINDOW_HOURS,
) -> float | None:
    """1.0 at the same instant, falling linearly to 0.0 at `window_hours`.

    Beyond the window the result is 0.0, which means "both times are known and
    they do not support a link" -- a different statement from absent.
    """
    if first is None or second is None:
        return None
    delta_hours = abs((second - first).total_seconds()) / 3600.0
    return max(0.0, 1.0 - delta_hours / window_hours)


def spatial_proximity(
    first: ObservationFeatures, second: ObservationFeatures, radius_km: float = DEFAULT_RADIUS_KM
) -> float | None:
    """1.0 at the same point, falling to 0.0 at `radius_km`."""
    if first.location is None or second.location is None:
        return None
    distance = haversine_km(
        first.location.lat, first.location.lon, second.location.lat, second.location.lon
    )
    return max(0.0, 1.0 - distance / radius_km)


def category_agreement(first: ObservationFeatures, second: ObservationFeatures) -> float | None:
    if first.category is None or second.category is None:
        return None
    return 1.0 if first.category == second.category else 0.0


def score_pair(
    first: ObservationFeatures,
    second: ObservationFeatures,
    *,
    temporal_window_hours: float = DEFAULT_TEMPORAL_WINDOW_HOURS,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> PairSuggestion | None:
    """Compare two observations. None when nothing at all can be compared."""
    if first.observation_id == second.observation_id:
        raise ValueError("a pair needs two different observations")

    raw: dict[str, float | None] = {
        "semantic_similarity": semantic_similarity(first, second),
        "temporal_proximity": temporal_proximity(
            first.observed_at, second.observed_at, temporal_window_hours
        ),
        "spatial_proximity": spatial_proximity(first, second, radius_km),
        "category_agreement": category_agreement(first, second),
    }

    components = {name: value for name, value in raw.items() if value is not None}
    missing = tuple(name for name, value in raw.items() if value is None)
    if not components:
        return None

    total_weight = sum(WEIGHTS[name] for name in components)
    score = sum(WEIGHTS[name] * value for name, value in components.items()) / total_weight

    source_independent = not (
        first.source_ref and second.source_ref and first.source_ref == second.source_ref
    )

    return PairSuggestion(
        observation_a_id=first.observation_id,
        observation_b_id=second.observation_id,
        score=score,
        components=components,
        missing_signals=tuple(MISSING_LABELS[name] for name in missing),
        reasons=_reasons(components, missing, source_independent),
        source_independent=source_independent,
    )


def _reasons(
    components: dict[str, float], missing: tuple[str, ...], source_independent: bool
) -> tuple[str, ...]:
    """Plain-language grounds for the suggestion. Wording states similarity of
    *reports*, never sameness of events and never a cause."""
    reasons: list[str] = []
    if components.get("semantic_similarity", 0.0) >= 0.34:
        reasons.append("the two reports use similar wording")
    if components.get("temporal_proximity", 0.0) >= 0.5:
        reasons.append("the two reports were made close in time")
    if components.get("spatial_proximity", 0.0) >= 0.5:
        reasons.append("the two reports place the observation close together")
    if components.get("category_agreement", 0.0) == 1.0:
        reasons.append("the two reports use the same category")
    if not source_independent:
        reasons.append(
            "both reports trace to the same original source, so they are not "
            "independent accounts of anything"
        )
    if missing:
        reasons.append(f"{len(missing)} signal(s) could not be used; see missing_signals")
    return tuple(reasons)


def rank(
    subject: ObservationFeatures,
    candidates: list[ObservationFeatures],
    *,
    ambiguity_margin: float = 0.05,
    **scoring_options: float,
) -> Ranking:
    """Score one observation against candidates, best first.

    Only pairwise results are produced here. Two results that share a middle
    observation are not merged, because A-looks-like-B and B-looks-like-C does
    not mean A-looks-like-C (`docs/files/22` section 9).
    """
    scored: list[PairSuggestion] = []
    for candidate in candidates:
        suggestion = score_pair(subject, candidate, **scoring_options)
        if suggestion is not None:
            scored.append(suggestion)
    scored.sort(key=lambda item: item.score, reverse=True)

    ambiguous = len(scored) > 1 and (scored[0].score - scored[1].score) <= ambiguity_margin
    return Ranking(subject.observation_id, tuple(scored), ambiguous)
