"""SQLAlchemy ORM models for the environmental data catalogue."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from ecowatch.core.spatial import GeographyType


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Source dataset with recorded rights and coverage, scoped to an organisation."""

    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("organisation_id", "name", name="uq_datasets_organisation_name"),
    )

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    owner: Mapped[str] = mapped_column("owner", String(200), nullable=False)
    licence: Mapped[str] = mapped_column("licence", String(200), nullable=False)
    attribution: Mapped[str] = mapped_column("attribution", Text, nullable=False)
    permittedUse: Mapped[str] = mapped_column("permitted_use", Text, nullable=False)
    crs: Mapped[str] = mapped_column("crs", String(50), nullable=False)
    coverageStartAt: Mapped[datetime | None] = mapped_column(
        "coverage_start_at", DateTime(timezone=True), nullable=True
    )
    coverageEndAt: Mapped[datetime | None] = mapped_column(
        "coverage_end_at", DateTime(timezone=True), nullable=True
    )
    coverageGeometry: Mapped[Any | None] = mapped_column(
        "coverage_geometry", GeographyType("GEOMETRY", 4326), nullable=True
    )


class DatasetVersion(Base, UUIDPrimaryKeyMixin):
    """Immutable snapshot of a dataset's provenance, rights, and processing context."""

    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_label", name="uq_dataset_versions_label"),
    )

    datasetId: Mapped[uuid.UUID] = mapped_column(
        "dataset_id",
        Uuid(as_uuid=True),
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )
    versionLabel: Mapped[str] = mapped_column("version_label", String(100), nullable=False)
    sourceAcquisitionAt: Mapped[datetime] = mapped_column(
        "source_acquisition_at", DateTime(timezone=True), nullable=False
    )
    resolution: Mapped[str] = mapped_column("resolution", String(100), nullable=False)
    crs: Mapped[str] = mapped_column("crs", String(50), nullable=False)
    method: Mapped[str] = mapped_column("method", Text, nullable=False)
    limitations: Mapped[str | None] = mapped_column("limitations", Text, nullable=True)
    qualityNotes: Mapped[str | None] = mapped_column("quality_notes", Text, nullable=True)
    licenceSnapshot: Mapped[str] = mapped_column("licence_snapshot", String(200), nullable=False)
    attributionSnapshot: Mapped[str] = mapped_column(
        "attribution_snapshot", Text, nullable=False
    )
    permittedUseSnapshot: Mapped[str] = mapped_column(
        "permitted_use_snapshot", Text, nullable=False
    )
    checksum: Mapped[str | None] = mapped_column("checksum", String(128), nullable=True)
    storageKey: Mapped[str | None] = mapped_column("storage_key", String(500), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
