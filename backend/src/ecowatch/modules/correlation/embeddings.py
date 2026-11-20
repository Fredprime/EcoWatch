"""Dependency-free vector inputs for the pgvector candidate prefilter.

Provider contract (ADR-019 remains open):

* ``hashed-words-v1`` is deterministic lexical word hashing. It is not a
  trained semantic model and carries no accuracy claim.
* ``imported-v1`` accepts a precomputed vector only from an operator-allowed
  internal source. Provenance is not validation, so it also carries no accuracy
  claim.

The provider is selected by deployment config, never by request input. Tenant
scoping stays in the storage layer; this module only builds bounded vectors and
provider/source-specific input hashes.

`shortcut: neither provider is the trained semantic model in ADR-019. Upgrade
only after the owner selects a model and a reviewed labelled set is evaluated.`
"""

from __future__ import annotations

import hashlib
import math
import os
from collections.abc import Sequence
from enum import StrEnum

from .scoring import tokens


class EmbeddingProvider(StrEnum):
    """Active vector provider. Neither member is a validated semantic model."""

    HASHED_WORDS = "hashed-words-v1"
    IMPORTED = "imported-v1"


EMBEDDING_PROVIDER_ENV = "ECOWATCH_EMBEDDING_PROVIDER"
IMPORT_SOURCES_ENV = "ECOWATCH_IMPORTED_EMBEDDING_SOURCES"
PROVIDER_IS_SEMANTIC: dict[EmbeddingProvider, bool] = {
    EmbeddingProvider.HASHED_WORDS: False,
    EmbeddingProvider.IMPORTED: False,
}


def _provider_from_env(value: str | None) -> EmbeddingProvider:
    """Fail closed on an unknown provider; never silently fall back to hashing."""
    configured = (value or "").strip() or EmbeddingProvider.HASHED_WORDS.value
    return EmbeddingProvider(configured)


EMBEDDING_PROVIDER = _provider_from_env(os.environ.get(EMBEDDING_PROVIDER_ENV))
VECTOR_MODEL_VERSION = EMBEDDING_PROVIDER.value
VECTOR_DIMENSIONS = 384


def is_semantic_provider(provider: EmbeddingProvider | None = None) -> bool:
    """Both current providers are non-semantic until ADR-019 is decided."""
    return PROVIDER_IS_SEMANTIC[
        EMBEDDING_PROVIDER if provider is None else provider
    ]


def embedding_terms(text: str | None, category: str | None) -> frozenset[str]:
    """The only text used to build an embedding: description plus category."""
    return tokens(f"{category or ''} {text or ''}")


def embedding_input_hash(
    text: str | None, category: str | None, *, source: str | None = None
) -> str:
    """Stable hash of the active provider, optional internal source and input.

    An importer must pass its trusted ``source`` so two sources cannot reuse the
    same stored vector for the same report text.
    """
    canonical = "\n".join(sorted(embedding_terms(text, category)))
    payload = "\0".join((VECTOR_MODEL_VERSION, source or "", canonical))
    return hashlib.sha256(payload.encode()).hexdigest()


def _trusted_import_sources() -> frozenset[str]:
    """Operator-configured internal source names; empty by default (path closed)."""
    raw = os.environ.get(IMPORT_SOURCES_ENV, "")
    return frozenset(name.strip() for name in raw.split(",") if name.strip())


def build_embedding(text: str | None, category: str | None) -> tuple[float, ...] | None:
    """Return a normalised hashed-word vector, or None when there is no text.

    Under the imported provider this returns None: a hashed vector must never be
    stored under a different provider's label, and the labelled keyword fallback
    stays available until an internal importer supplies a vector.
    """
    if EMBEDDING_PROVIDER is not EmbeddingProvider.HASHED_WORDS:
        return None
    terms = embedding_terms(text, category)
    if not terms:
        return None

    values = [0.0] * VECTOR_DIMENSIONS
    for term in terms:
        digest = hashlib.sha256(term.encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSIONS
        values[bucket] += 1.0
    norm = math.sqrt(math.fsum(value * value for value in values))
    return tuple(value / norm for value in values)


def build_embedding_from_precomputed(
    vector: Sequence[float], *, source: str
) -> tuple[float, ...]:
    """Validate an imported vector from an operator-allowed internal source.

    Call only from internal import code with a source from deployment config.
    Never pass request data or model output here: neither is a trusted source.
    The returned vector is a ranking input, not a semantic accuracy claim.

    `shortcut: no import job is wired yet. This is the gate and validation an
    internal importer must use, with ``embedding_input_hash(..., source=...)``.`
    """
    if EMBEDDING_PROVIDER is not EmbeddingProvider.IMPORTED:
        raise ValueError("precomputed vectors require the imported provider")
    if not isinstance(source, str) or source not in _trusted_import_sources():
        raise ValueError("vector source is not an allowed internal import source")
    if isinstance(vector, (str, bytes)) or not isinstance(vector, Sequence):
        raise ValueError("precomputed vector must be a numeric sequence")
    if len(vector) != VECTOR_DIMENSIONS:
        raise ValueError(f"precomputed vector must have {VECTOR_DIMENSIONS} dimensions")
    if any(isinstance(value, bool) for value in vector):
        raise ValueError("precomputed vector must not contain booleans")
    try:
        values = tuple(float(value) for value in vector)
    except (TypeError, ValueError) as exc:
        raise ValueError("precomputed vector must contain only finite numbers") from exc
    if not all(math.isfinite(value) for value in values):
        raise ValueError("precomputed vector must contain only finite numbers")
    norm = math.sqrt(math.fsum(value * value for value in values))
    if norm == 0.0:
        raise ValueError("precomputed vector must have a non-zero norm")
    return tuple(value / norm for value in values)
