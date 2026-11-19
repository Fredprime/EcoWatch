"""Unit checks for hashed-word vectors and the labelled keyword fallback.

Vectors here are deterministic lexical inputs for the pgvector storage path, not
a validated semantic model. These tests check wiring and bounds only, never
correlation accuracy (`ADR-019`, `ADR-030`).
"""

import math

from ecowatch.modules.correlation.embeddings import (
    VECTOR_DIMENSIONS,
    build_embedding,
    embedding_input_hash,
)
from ecowatch.modules.correlation.features import ObservationFeatures
from ecowatch.modules.correlation.scoring import (
    semantic_similarity,
    token_similarity,
    vector_similarity,
)


def test_build_embedding_is_normalised_and_deterministic() -> None:
    first = build_embedding("dead fish at the weir", "water_pollution")
    second = build_embedding("dead fish at the weir", "water_pollution")

    assert first is not None and second is not None
    assert first == second
    assert len(first) == VECTOR_DIMENSIONS
    assert math.isclose(math.fsum(value * value for value in first), 1.0, abs_tol=1e-9)


def test_build_embedding_returns_none_without_text() -> None:
    assert build_embedding(None, None) is None
    assert build_embedding("   ", None) is None


def test_input_hash_is_stable_and_text_sensitive() -> None:
    first = embedding_input_hash("dead fish at the weir", "water_pollution")
    assert first == embedding_input_hash("dead fish at the weir", "water_pollution")
    assert first != embedding_input_hash("oily sheen at the bend", "water_pollution")


def test_vector_similarity_bounds_and_absence() -> None:
    assert vector_similarity((1.0, 0.0), (1.0, 0.0)) == 1.0
    assert vector_similarity((1.0, 0.0), (-1.0, 0.0)) == 0.0  # clamped from -1
    assert vector_similarity((1.0, 0.0), None) is None
    assert vector_similarity((1.0, 0.0), (1.0,)) is None  # dimension mismatch


def test_semantic_similarity_falls_back_to_tokens_without_vectors() -> None:
    first = ObservationFeatures("a", text="dead fish near the weir")
    second = ObservationFeatures("b", text="dead fish near the weir")

    assert semantic_similarity(first, second) == token_similarity(first.text, second.text)


def test_semantic_similarity_uses_vectors_when_present() -> None:
    vector = (1.0, 0.0, 0.0)
    first = ObservationFeatures("a", text="zebra migration", embedding=vector)
    second = ObservationFeatures("b", text="copper refinery", embedding=vector)

    assert token_similarity(first.text, second.text) == 0.0
    assert semantic_similarity(first, second) == 1.0  # vector path, not the fallback
