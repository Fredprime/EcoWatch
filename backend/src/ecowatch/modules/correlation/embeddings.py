"""Dependency-free vector inputs for the pgvector candidate prefilter.

The embedding model is still an open item (ADR-019). This deterministic hashed
word vector is a bounded lexical representation, not a validated semantic model
and not an accuracy claim. It gives pgvector a stable input so the storage and
candidate path can be tested while a model choice remains open.

`shortcut: word hashing, not learned embeddings. Replace with the approved
semantic model when ADR-019 is decided.`
"""

from __future__ import annotations

import hashlib
import math

from .scoring import tokens

VECTOR_MODEL_VERSION = "hashed-words-v1"
VECTOR_DIMENSIONS = 384


def embedding_terms(text: str | None, category: str | None) -> frozenset[str]:
    """The only text used to build an embedding: description plus category."""
    return tokens(f"{category or ''} {text or ''}")


def embedding_input_hash(text: str | None, category: str | None) -> str:
    """Stable hash of the model version and the exact embedding input."""
    canonical = "\n".join(sorted(embedding_terms(text, category)))
    payload = f"{VECTOR_MODEL_VERSION}\0{canonical}".encode()
    return hashlib.sha256(payload).hexdigest()


def build_embedding(text: str | None, category: str | None) -> tuple[float, ...] | None:
    """Return a normalised hashed-word vector, or None when there is no text."""
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
