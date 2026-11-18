"""SQLAlchemy ORM models for Phase 2 evidence correlation.

A row is a *suggestion* or a *decision about a suggestion*. It is never a
conclusion: no field here says a source caused anything, that harm occurred, or
that two reports are the same event.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ecowatch.core.vector import VectorType
from ecowatch.modules.correlation.embeddings import VECTOR_DIMENSIONS, VECTOR_MODEL_VERSION


class CorrelationTask(StrEnum):
    """What a pairwise suggestion is claiming to look for."""

    DUPLICATE = "duplicate"
    SAME_EVENT = "same_event"
    SOURCE_DEPENDENCY = "source_dependency"
    CROSS_CASE = "cross_case"


class RelationshipStatus(StrEnum):
    """Lifecycle of a suggestion, all reachable only through review.

    There is no `confirmed` or `verified` member on purpose: confirming an
    incident is a case action with its own permissions and audit trail.
    """

    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


class CorrelationEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One stored text vector for an observation, model version and input hash.

    The input hash is what makes a rescan skip re-writing an unchanged vector.
    Nothing here claims the vector is a semantic truth: it is an input to a
    reviewer-facing candidate prefilter only.
    """

    __tablename__ = "correlation_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "model_version",
            "input_hash",
            name="uq_correlation_embeddings_observation_model_input",
        ),
    )

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
    modelVersion: Mapped[str] = mapped_column(
        "model_version", String(32), nullable=False, default=VECTOR_MODEL_VERSION
    )
    inputHash: Mapped[str] = mapped_column("input_hash", String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        "embedding", VectorType(VECTOR_DIMENSIONS), nullable=False
    )


class EvidenceRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One pairwise suggestion with its reasons, and the human decision on it."""

    __tablename__ = "evidence_relationships"
    __table_args__ = (
        UniqueConstraint(
            "observation_a_id",
            "observation_b_id",
            "task",
            name="uq_evidence_relationships_pair_task",
        ),
        # Canonical ordering is what makes rejection an index probe instead of a
        # rescan, and what stops the same pair being stored twice with the
        # ends swapped. The database refuses unordered pairs outright.
        CheckConstraint(
            "observation_a_id < observation_b_id",
            name="ck_evidence_relationships_ordered",
        ),
        CheckConstraint(
            "observation_a_id <> observation_b_id",
            name="ck_evidence_relationships_distinct",
        ),
    )

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    observationAId: Mapped[uuid.UUID] = mapped_column(
        "observation_a_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
    observationBId: Mapped[uuid.UUID] = mapped_column(
        "observation_b_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
    task: Mapped[str] = mapped_column(
        "task", String(32), nullable=False, default=CorrelationTask.SAME_EVENT.value
    )
    score: Mapped[float] = mapped_column("score", Float, nullable=False)
    components: Mapped[dict[str, float]] = mapped_column(
        "components", JSON, nullable=False, default=dict
    )
    missingSignals: Mapped[list[str]] = mapped_column(
        "missing_signals", JSON, nullable=False, default=list
    )
    reasons: Mapped[list[str]] = mapped_column("reasons", JSON, nullable=False, default=list)
    methodVersion: Mapped[str] = mapped_column("method_version", String(32), nullable=False)
    sourceIndependent: Mapped[bool] = mapped_column(
        "source_independent", Boolean, nullable=False, default=True
    )
    status: Mapped[str] = mapped_column(
        "status",
        String(32),
        nullable=False,
        default=RelationshipStatus.SUGGESTED.value,
        index=True,
    )
    decidedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "decided_by_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    decidedAt: Mapped[datetime | None] = mapped_column(
        "decided_at", DateTime(timezone=True), nullable=True
    )
    decisionReason: Mapped[str | None] = mapped_column(
        "decision_reason", Text, nullable=True
    )
    # Set when this suggestion was tied with another for the same subject. The
    # engine never breaks a tie silently, so the flag travels with the row.
    ambiguous: Mapped[bool] = mapped_column(
        "ambiguous", Boolean, nullable=False, default=False
    )


class CorrelationCluster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A provisional grouping of reports. Staff-only, and not a case.

    Nothing here promotes a cluster or links it to a case: that is a separate
    action with its own permission and audit trail. A cluster exists so a
    reviewer has something to look at while deciding, and so `merge`/`split`/
    `promote_to_case` have a subject once they are built.
    """

    __tablename__ = "correlation_clusters"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )


class CorrelationClusterMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One observation in one provisional cluster.

    `observation_id` is unique: a report belongs to at most one cluster, which is
    what stops A~B and B~C quietly becoming a three-member cluster. Membership
    only grows when a person accepts a relationship, never because two scores
    happened to be close (`docs/files/22` section 9).
    """

    __tablename__ = "correlation_cluster_members"
    __table_args__ = (
        UniqueConstraint("observation_id", name="uq_correlation_cluster_members_observation"),
    )

    clusterId: Mapped[uuid.UUID] = mapped_column(
        "cluster_id",
        Uuid(as_uuid=True),
        ForeignKey("correlation_clusters.id"),
        nullable=False,
        index=True,
    )
    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
