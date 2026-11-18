"""SQLAlchemy ORM models for indicators, verification, and approved publications."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class IndicatorDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Organisation-scoped, versioned measurement indicator definition."""

    __tablename__ = "indicator_definitions"
    __table_args__ = (
        UniqueConstraint("organisation_id", "code", name="uq_indicator_definitions_code"),
    )

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column("code", String(50), nullable=False)
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    domain: Mapped[str] = mapped_column("domain", String(50), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    unitId: Mapped[uuid.UUID] = mapped_column(
        "unit_id", Uuid(as_uuid=True), ForeignKey("units.id"), nullable=False
    )
    methodName: Mapped[str] = mapped_column("method_name", String(200), nullable=False)
    methodVersion: Mapped[str] = mapped_column("method_version", String(100), nullable=False)
    criteriaVersion: Mapped[str | None] = mapped_column(
        "criteria_version", String(100), nullable=True
    )
    approvedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "approved_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approvedAt: Mapped[datetime | None] = mapped_column(
        "approved_at", DateTime(timezone=True), nullable=True
    )


class IndicatorMeasurement(Base, UUIDPrimaryKeyMixin):
    """Qualified indicator measurement with unit, method, and detection limit."""

    __tablename__ = "indicator_measurements"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    indicatorDefinitionId: Mapped[uuid.UUID] = mapped_column(
        "indicator_definition_id",
        Uuid(as_uuid=True),
        ForeignKey("indicator_definitions.id"),
        nullable=False,
        index=True,
    )
    interventionId: Mapped[uuid.UUID | None] = mapped_column(
        "intervention_id",
        Uuid(as_uuid=True),
        ForeignKey("interventions.id"),
        nullable=True,
        index=True,
    )
    caseId: Mapped[uuid.UUID | None] = mapped_column(
        "case_id", Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
    observationId: Mapped[uuid.UUID | None] = mapped_column(
        "observation_id", Uuid(as_uuid=True), ForeignKey("observations.id"), nullable=True
    )
    measuredAt: Mapped[datetime] = mapped_column(
        "measured_at", DateTime(timezone=True), nullable=False
    )
    value: Mapped[Decimal | None] = mapped_column("value", Numeric(20, 6), nullable=True)
    qualifier: Mapped[str] = mapped_column("qualifier", String(20), nullable=False)
    detectionLimit: Mapped[Decimal | None] = mapped_column(
        "detection_limit", Numeric(20, 6), nullable=True
    )
    unitId: Mapped[uuid.UUID] = mapped_column(
        "unit_id", Uuid(as_uuid=True), ForeignKey("units.id"), nullable=False
    )
    methodName: Mapped[str] = mapped_column("method_name", String(200), nullable=False)
    methodVersion: Mapped[str] = mapped_column("method_version", String(100), nullable=False)
    qualityControls: Mapped[str | None] = mapped_column(
        "quality_controls", Text, nullable=True
    )
    uncertaintyNote: Mapped[str | None] = mapped_column(
        "uncertainty_note", Text, nullable=True
    )
    source: Mapped[str | None] = mapped_column("source", Text, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class VerificationAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Assessment of whether an intervention's observed outcome meets criteria."""

    __tablename__ = "verification_assessments"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    interventionId: Mapped[uuid.UUID] = mapped_column(
        "intervention_id",
        Uuid(as_uuid=True),
        ForeignKey("interventions.id"),
        nullable=False,
        index=True,
    )
    baselineMeasurementIds: Mapped[list[str]] = mapped_column(
        "baseline_measurement_ids", JSON, nullable=False, default=list
    )
    followUpMeasurementIds: Mapped[list[str]] = mapped_column(
        "follow_up_measurement_ids", JSON, nullable=False, default=list
    )
    comparisonMethod: Mapped[str] = mapped_column("comparison_method", Text, nullable=False)
    confounders: Mapped[str | None] = mapped_column("confounders", Text, nullable=True)
    seasonalityNotes: Mapped[str | None] = mapped_column(
        "seasonality_notes", Text, nullable=True
    )
    uncertaintyNote: Mapped[str | None] = mapped_column(
        "uncertainty_note", Text, nullable=True
    )
    conclusion: Mapped[str] = mapped_column("conclusion", String(30), nullable=False)
    criteriaVersion: Mapped[str | None] = mapped_column(
        "criteria_version", String(100), nullable=True
    )
    status: Mapped[str] = mapped_column("status", String(20), nullable=False, default="draft")
    reviewedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "reviewed_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewedAt: Mapped[datetime | None] = mapped_column(
        "reviewed_at", DateTime(timezone=True), nullable=True
    )


class Publication(Base, UUIDPrimaryKeyMixin):
    """Approved public summary that never exposes sensitive data or identities."""

    __tablename__ = "publications"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    verificationAssessmentId: Mapped[uuid.UUID | None] = mapped_column(
        "verification_assessment_id",
        Uuid(as_uuid=True),
        ForeignKey("verification_assessments.id"),
        nullable=True,
    )
    caseId: Mapped[uuid.UUID | None] = mapped_column(
        "case_id", Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
    publishedText: Mapped[str] = mapped_column("published_text", Text, nullable=False)
    approvedByUserId: Mapped[uuid.UUID] = mapped_column(
        "approved_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approvedRole: Mapped[str] = mapped_column("approved_role", String(50), nullable=False)
    approvedAt: Mapped[datetime] = mapped_column(
        "approved_at", DateTime(timezone=True), nullable=False
    )
    retractedAt: Mapped[datetime | None] = mapped_column(
        "retracted_at", DateTime(timezone=True), nullable=True
    )
    retractionReason: Mapped[str | None] = mapped_column(
        "retraction_reason", Text, nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
