"""Unit checks for hashed-word vectors and the labelled keyword fallback.

Vectors here are deterministic lexical inputs for the pgvector storage path, not
a validated semantic model. These tests check wiring and bounds only, never
correlation accuracy (`ADR-019`, `ADR-030`).
"""

import math

import pytest

from ecowatch.modules.correlation import embeddings
from ecowatch.modules.correlation.embeddings import (
    EMBEDDING_PROVIDER,
    VECTOR_DIMENSIONS,
    VECTOR_MODEL_VERSION,
    EmbeddingProvider,
    _provider_from_env,
    build_embedding,
    build_embedding_from_precomputed,
    embedding_input_hash,
    is_semantic_provider,
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


def test_provider_contract_labels_both_providers_non_semantic() -> None:
    assert EMBEDDING_PROVIDER is EmbeddingProvider.HASHED_WORDS
    assert EmbeddingProvider.HASHED_WORDS.value == VECTOR_MODEL_VERSION
    assert is_semantic_provider() is False
    assert is_semantic_provider(EmbeddingProvider.IMPORTED) is False
    assert _provider_from_env("imported-v1") is EmbeddingProvider.IMPORTED
    with pytest.raises(ValueError):
        _provider_from_env("unknown-model")


def test_input_hash_separates_provider_and_internal_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text, category = "dead fish at the weir", "water_pollution"
    hashed = embedding_input_hash(text, category)
    assert hashed == embedding_input_hash(text, category)

    monkeypatch.setattr(embeddings, "VECTOR_MODEL_VERSION", EmbeddingProvider.IMPORTED.value)
    firstImport = embedding_input_hash(text, category, source="internal-import")
    assert firstImport != hashed
    assert firstImport != embedding_input_hash(text, category, source="other-import")


def test_precomputed_vectors_require_active_provider_and_trusted_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector = (1.0, *([0.0] * (VECTOR_DIMENSIONS - 1)))
    with pytest.raises(ValueError, match="imported provider"):
        build_embedding_from_precomputed(vector, source="internal-import")

    monkeypatch.setattr(embeddings, "EMBEDDING_PROVIDER", EmbeddingProvider.IMPORTED)
    monkeypatch.setenv(embeddings.IMPORT_SOURCES_ENV, "internal-import, other-import")
    for source in ("request-body", "", 123):
        with pytest.raises(ValueError, match="not an allowed internal import source"):
            build_embedding_from_precomputed(vector, source=source)  # type: ignore[arg-type]
    # No hashed vector may be stored under the imported provider's label.
    assert build_embedding("dead fish at the weir", "water_pollution") is None

    imported = build_embedding_from_precomputed(vector, source="other-import")
    assert len(imported) == VECTOR_DIMENSIONS
    assert math.isclose(math.fsum(value * value for value in imported), 1.0, abs_tol=1e-9)


@pytest.mark.parametrize(
    "badVector",
    [
        (1.0,),
        (float("nan"), *([0.0] * (VECTOR_DIMENSIONS - 1))),
        (float("inf"), *([0.0] * (VECTOR_DIMENSIONS - 1))),
        (0.0,) * VECTOR_DIMENSIONS,
        ("not a number", *([0.0] * (VECTOR_DIMENSIONS - 1))),
        (True, *([0.0] * (VECTOR_DIMENSIONS - 1))),
        "not a sequence",
    ],
)
def test_precomputed_vector_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch, badVector: object
) -> None:
    monkeypatch.setattr(embeddings, "EMBEDDING_PROVIDER", EmbeddingProvider.IMPORTED)
    monkeypatch.setenv(embeddings.IMPORT_SOURCES_ENV, "internal-import")

    with pytest.raises(ValueError):
        build_embedding_from_precomputed(badVector, source="internal-import")  # type: ignore[arg-type]


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
