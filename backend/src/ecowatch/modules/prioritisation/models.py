"""SQLAlchemy ORM model for evidence-honest prioritisation assessments."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PrioritisationAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recorded prioritisation factors, missing inputs, and human decision."""

    __tablename__ = "prioritisation_assessments"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    caseId: Mapped[uuid.UUID] = mapped_column(
        "case_id", Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    assessmentAt: Mapped[datetime] = mapped_column(
        "assessment_at", DateTime(timezone=True), nullable=False
    )
    methodName: Mapped[str] = mapped_column("method_name", String(200), nullable=False)
    methodVersion: Mapped[str] = mapped_column("method_version", String(100), nullable=False)
    factors: Mapped[dict[str, Any]] = mapped_column("factors", JSON, nullable=False)
    missingInputs: Mapped[list[str]] = mapped_column(
        "missing_inputs", JSON, nullable=False, default=list
    )
    compositeRank: Mapped[Decimal | None] = mapped_column(
        "composite_rank", Numeric(12, 4), nullable=True
    )
    rankingMethodRef: Mapped[str | None] = mapped_column(
        "ranking_method_ref", Text, nullable=True
    )
    rankIsNotSeverity: Mapped[bool | None] = mapped_column(
        "rank_is_not_severity", Boolean, nullable=True
    )
    decision: Mapped[str | None] = mapped_column("decision", String(20), nullable=True)
    decisionRationale: Mapped[str | None] = mapped_column(
        "decision_rationale", Text, nullable=True
    )
    decidedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "decided_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    decidedAt: Mapped[datetime | None] = mapped_column(
        "decided_at", DateTime(timezone=True), nullable=True
    )
    reviewerUserId: Mapped[uuid.UUID | None] = mapped_column(
        "reviewer_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewedAt: Mapped[datetime | None] = mapped_column(
        "reviewed_at", DateTime(timezone=True), nullable=True
    )
