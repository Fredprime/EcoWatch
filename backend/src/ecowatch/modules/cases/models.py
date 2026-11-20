"""SQLAlchemy ORM models and enumerations for environmental investigation cases."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ecowatch.core.spatial import GeographyType


class CaseStatus(StrEnum):
    """Candidate case lifecycle statuses from docs/12 §6."""

    NEW_UNREVIEWED = "new_unreviewed"
    INITIAL_REVIEW = "initial_review"
    EVIDENCE_GATHERING = "evidence_gathering"
    CORROBORATED_EVIDENCE_AVAILABLE = "corroborated_evidence_available"
    FIELD_VERIFICATION_REQUIRED = "field_verification_required"
    FIELD_VERIFIED = "field_verified"
    REFERRED_TO_AUTHORITY = "referred_to_authority"
    UNDER_INTERVENTION = "under_intervention"
    MONITORING_OUTCOMES = "monitoring_outcomes"
    RECOVERY_VERIFIED = "recovery_verified"
    NOT_SUBSTANTIATED = "not_substantiated"
    CLOSED = "closed"
    MERGED = "merged"


class LinkProposedBy(StrEnum):
    """Origin of a case-to-observation link proposal."""

    HUMAN = "human"
    WORKFLOW = "workflow"


class LinkReviewStatus(StrEnum):
    """Human review status for a case-to-observation link."""

    ACCEPTED = "accepted"
    CONTESTED = "contested"
    REJECTED = "rejected"


class Case(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Managed environmental investigation record scoped to an organisation."""

    __tablename__ = "cases"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    caseCode: Mapped[str] = mapped_column("case_code", String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column("title", String(200), nullable=False)
    summary: Mapped[str] = mapped_column("summary", Text, nullable=False)
    status: Mapped[str] = mapped_column(
        "status",
        String(64),
        nullable=False,
        default=CaseStatus.NEW_UNREVIEWED.value,
        index=True,
    )
    statusRationale: Mapped[str] = mapped_column("status_rationale", Text, nullable=False)
    areaGeometry: Mapped[Any | None] = mapped_column(
        "area_geometry", GeographyType("GEOMETRY", 4326), nullable=True
    )
    publicGeometry: Mapped[Any | None] = mapped_column(
        "public_geometry", GeographyType("GEOMETRY", 4326), nullable=True
    )
    areaReference: Mapped[str | None] = mapped_column("area_reference", String(200), nullable=True)
    leadInvestigatorId: Mapped[uuid.UUID | None] = mapped_column(
        "lead_investigator_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    investigationQuestions: Mapped[list[str]] = mapped_column(
        "investigation_questions", JSON, nullable=False, default=list
    )
    competingHypotheses: Mapped[list[str]] = mapped_column(
        "competing_hypotheses", JSON, nullable=False, default=list
    )
    evidenceGaps: Mapped[list[str]] = mapped_column(
        "evidence_gaps", JSON, nullable=False, default=list
    )
    referralRecord: Mapped[dict[str, Any] | None] = mapped_column(
        "referral_record", JSON, nullable=True
    )
    fieldRecordReference: Mapped[str | None] = mapped_column(
        "field_record_reference", String(200), nullable=True
    )
    specialistApprovalUserId: Mapped[uuid.UUID | None] = mapped_column(
        "specialist_approval_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    authorityApprovalUserId: Mapped[uuid.UUID | None] = mapped_column(
        "authority_approval_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    specialistApproverUserId: Mapped[uuid.UUID | None] = mapped_column(
        "specialist_approver_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    authorityApproverUserId: Mapped[uuid.UUID | None] = mapped_column(
        "authority_approver_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    twoKeyApprovedAt: Mapped[datetime | None] = mapped_column(
        "two_key_approved_at", DateTime(timezone=True), nullable=True
    )
    mergedIntoCaseId: Mapped[uuid.UUID | None] = mapped_column(
        "merged_into_case_id", Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
    accessClass: Mapped[str] = mapped_column(
        "access_class", String(32), nullable=False, default="internal"
    )
    isPublicSummaryApproved: Mapped[bool] = mapped_column(
        "is_public_summary_approved", Boolean, nullable=False, default=False
    )
    publicSummary: Mapped[str | None] = mapped_column("public_summary", Text, nullable=True)
    createdByUserId: Mapped[uuid.UUID] = mapped_column(
        "created_by_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    lastReviewedAt: Mapped[datetime | None] = mapped_column(
        "last_reviewed_at", DateTime(timezone=True), nullable=True
    )


class CaseObservation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Many-to-many link between a case and an observation with rationale and review state."""

    __tablename__ = "case_observations"
    __table_args__ = (
        UniqueConstraint("case_id", "observation_id", name="uq_case_observations_case_obs"),
    )

    caseId: Mapped[uuid.UUID] = mapped_column(
        "case_id",
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
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
    linkRationale: Mapped[str] = mapped_column("link_rationale", Text, nullable=False)
    proposedByType: Mapped[str] = mapped_column(
        "proposed_by_type",
        String(32),
        nullable=False,
        default=LinkProposedBy.HUMAN.value,
    )
    proposedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "proposed_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewStatus: Mapped[str] = mapped_column(
        "review_status",
        String(32),
        nullable=False,
        default=LinkReviewStatus.ACCEPTED.value,
    )
    reviewedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "reviewed_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewedAt: Mapped[datetime | None] = mapped_column(
        "reviewed_at", DateTime(timezone=True), nullable=True
    )
    isContested: Mapped[bool] = mapped_column(
        "is_contested", Boolean, nullable=False, default=False
    )
    contestedNote: Mapped[str | None] = mapped_column("contested_note", Text, nullable=True)
