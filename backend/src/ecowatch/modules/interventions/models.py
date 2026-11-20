"""SQLAlchemy ORM models for interventions and their delivery milestones."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ecowatch.core.spatial import GeographyType


class Intervention(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authorised response activity linked to one or more investigation cases."""

    __tablename__ = "interventions"

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
    additionalCaseIds: Mapped[list[str]] = mapped_column(
        "additional_case_ids", JSON, nullable=False, default=list
    )
    objective: Mapped[str] = mapped_column("objective", Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column("rationale", Text, nullable=True)
    responsibleOrganisationId: Mapped[uuid.UUID] = mapped_column(
        "responsible_organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
    )
    authorisedLeadUserId: Mapped[uuid.UUID] = mapped_column(
        "authorised_lead_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    proposedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "proposed_by_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    approvalReference: Mapped[str | None] = mapped_column(
        "approval_reference", Text, nullable=True
    )
    location: Mapped[Any | None] = mapped_column(
        "location", GeographyType("GEOMETRY", 4326), nullable=True
    )
    affectedAreaNotes: Mapped[str | None] = mapped_column(
        "affected_area_notes", Text, nullable=True
    )
    plannedStartAt: Mapped[datetime | None] = mapped_column(
        "planned_start_at", DateTime(timezone=True), nullable=True
    )
    plannedEndAt: Mapped[datetime | None] = mapped_column(
        "planned_end_at", DateTime(timezone=True), nullable=True
    )
    actualStartAt: Mapped[datetime | None] = mapped_column(
        "actual_start_at", DateTime(timezone=True), nullable=True
    )
    actualEndAt: Mapped[datetime | None] = mapped_column(
        "actual_end_at", DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        "status", String(30), nullable=False, default="proposed", index=True
    )
    resourcesNotes: Mapped[str | None] = mapped_column("resources_notes", Text, nullable=True)
    intendedOutcome: Mapped[str | None] = mapped_column(
        "intended_outcome", Text, nullable=True
    )
    indicatorDefinitionIds: Mapped[list[str]] = mapped_column(
        "indicator_definition_ids", JSON, nullable=False, default=list
    )
    baselineSummary: Mapped[str | None] = mapped_column(
        "baseline_summary", Text, nullable=True
    )
    risks: Mapped[str | None] = mapped_column("risks", Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column("limitations", Text, nullable=True)
    followUpSchedule: Mapped[str | None] = mapped_column(
        "follow_up_schedule", Text, nullable=True
    )
    verificationAssessmentId: Mapped[uuid.UUID | None] = mapped_column(
        "verification_assessment_id", Uuid(as_uuid=True), nullable=True
    )


class InterventionMilestone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Planned or completed delivery milestone for an intervention."""

    __tablename__ = "intervention_milestones"

    interventionId: Mapped[uuid.UUID] = mapped_column(
        "intervention_id",
        Uuid(as_uuid=True),
        ForeignKey("interventions.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    plannedAt: Mapped[datetime | None] = mapped_column(
        "planned_at", DateTime(timezone=True), nullable=True
    )
    completedAt: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        "status", String(20), nullable=False, default="planned"
    )
    evidenceAssetIds: Mapped[list[str]] = mapped_column(
        "evidence_asset_ids", JSON, nullable=False, default=list
    )
