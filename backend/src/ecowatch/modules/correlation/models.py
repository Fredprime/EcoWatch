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
