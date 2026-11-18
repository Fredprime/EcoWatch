"""SQLAlchemy ORM models for environmental intelligence and analysis provenance."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from ecowatch.core.spatial import GeographyType


class EnvironmentalEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Spatial or conceptual environmental entity used to relate observations."""

    __tablename__ = "environmental_entities"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    entityType: Mapped[str] = mapped_column("entity_type", String(50), nullable=False)
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    geometry: Mapped[Any | None] = mapped_column(
        "geometry", GeographyType("GEOMETRY", 4326), nullable=True
    )
    crs: Mapped[str] = mapped_column("crs", String(50), nullable=False, default="EPSG:4326")
    parentEntityId: Mapped[uuid.UUID | None] = mapped_column(
        "parent_entity_id",
        Uuid(as_uuid=True),
        ForeignKey("environmental_entities.id"),
        nullable=True,
    )


class EnvironmentalRelationship(Base, UUIDPrimaryKeyMixin):
    """Evidence-backed relationship between entities or observations with uncertainty."""

    __tablename__ = "environmental_relationships"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    relationshipType: Mapped[str] = mapped_column(
        "relationship_type", String(50), nullable=False
    )
    fromEntityId: Mapped[uuid.UUID | None] = mapped_column(
        "from_entity_id",
        Uuid(as_uuid=True),
        ForeignKey("environmental_entities.id"),
        nullable=True,
    )
    fromObservationId: Mapped[uuid.UUID | None] = mapped_column(
        "from_observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=True,
    )
    toEntityId: Mapped[uuid.UUID | None] = mapped_column(
        "to_entity_id",
        Uuid(as_uuid=True),
        ForeignKey("environmental_entities.id"),
        nullable=True,
    )
    toObservationId: Mapped[uuid.UUID | None] = mapped_column(
        "to_observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=True,
    )
    spatialScope: Mapped[str | None] = mapped_column("spatial_scope", Text, nullable=True)
    temporalStartAt: Mapped[datetime | None] = mapped_column(
        "temporal_start_at", DateTime(timezone=True), nullable=True
    )
    temporalEndAt: Mapped[datetime | None] = mapped_column(
        "temporal_end_at", DateTime(timezone=True), nullable=True
    )
    evidenceSummary: Mapped[str] = mapped_column("evidence_summary", Text, nullable=False)
    supportingEvidenceAssetIds: Mapped[list[str]] = mapped_column(
        "supporting_evidence_asset_ids", JSON, nullable=False, default=list
    )
    methodName: Mapped[str] = mapped_column("method_name", String(200), nullable=False)
    methodVersion: Mapped[str] = mapped_column("method_version", String(100), nullable=False)
    uncertainty: Mapped[str] = mapped_column("uncertainty", String(20), nullable=False)
    uncertaintyNote: Mapped[str] = mapped_column("uncertainty_note", Text, nullable=False)
    alternativeExplanations: Mapped[str] = mapped_column(
        "alternative_explanations", Text, nullable=False
    )
    reviewState: Mapped[str] = mapped_column(
        "review_state", String(20), nullable=False, default="proposed"
    )
    reviewedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "reviewed_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewedAt: Mapped[datetime | None] = mapped_column(
        "reviewed_at", DateTime(timezone=True), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class AnalysisRun(Base, UUIDPrimaryKeyMixin):
    """Reproducible record of a spatial or statistical analysis request."""

    __tablename__ = "analysis_runs"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    caseId: Mapped[uuid.UUID | None] = mapped_column(
        "case_id", Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column("question", Text, nullable=False)
    analysisType: Mapped[str] = mapped_column("analysis_type", String(50), nullable=False)
    methodName: Mapped[str] = mapped_column("method_name", String(200), nullable=False)
    methodVersion: Mapped[str] = mapped_column("method_version", String(100), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column("parameters", JSON, nullable=False)
    inputDatasetVersionIds: Mapped[list[str]] = mapped_column(
        "input_dataset_version_ids", JSON, nullable=False
    )
    crs: Mapped[str] = mapped_column("crs", String(50), nullable=False)
    qualityMaskNotes: Mapped[str | None] = mapped_column(
        "quality_mask_notes", Text, nullable=True
    )
    seasonalContext: Mapped[str | None] = mapped_column(
        "seasonal_context", Text, nullable=True
    )
    limitations: Mapped[str] = mapped_column("limitations", Text, nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String(20), nullable=False, default="queued", index=True
    )
    requestedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "requested_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    startedAt: Mapped[datetime | None] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completedAt: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    failureReason: Mapped[str | None] = mapped_column("failure_reason", Text, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class AnalysisOutput(Base, UUIDPrimaryKeyMixin):
    """Derived output of an analysis run, pending human interpretation."""

    __tablename__ = "analysis_outputs"

    analysisRunId: Mapped[uuid.UUID] = mapped_column(
        "analysis_run_id",
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id"),
        nullable=False,
        index=True,
    )
    outputType: Mapped[str] = mapped_column("output_type", String(20), nullable=False)
    summary: Mapped[str] = mapped_column("summary", Text, nullable=False)
    storageKey: Mapped[str | None] = mapped_column("storage_key", String(500), nullable=True)
    isDerived: Mapped[bool] = mapped_column("is_derived", Boolean, nullable=False, default=True)
    derivedFromObservationIds: Mapped[list[str]] = mapped_column(
        "derived_from_observation_ids", JSON, nullable=False, default=list
    )
    interpretationState: Mapped[str] = mapped_column(
        "interpretation_state", String(30), nullable=False, default="pending_review"
    )
    limitations: Mapped[str] = mapped_column("limitations", Text, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
