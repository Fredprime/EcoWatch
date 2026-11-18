"""SQLAlchemy ORM models for evidence assets and EXIF-stripped derivatives."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, UUIDPrimaryKeyMixin, utc_now
from ecowatch.modules.observations.models import AccessClass


class ScanStatus(StrEnum):
    """Security scan status for uploaded evidence assets."""

    PENDING = "pending"
    CLEAN = "clean"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


class MetadataExtractionStatus(StrEnum):
    """Extraction outcome for embedded image/file metadata."""

    PENDING = "pending"
    EXTRACTED = "extracted"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class DerivativeType(StrEnum):
    """Supported derived media representations stored separately from originals."""

    EXIF_STRIPPED_PREVIEW = "exif_stripped_preview"
    THUMBNAIL = "thumbnail"


class EvidenceAsset(Base, UUIDPrimaryKeyMixin):
    """Original untouched evidence file record under restricted application-mediated access."""

    __tablename__ = "evidence_assets"

    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    storageKey: Mapped[str] = mapped_column(
        "storage_key", String(255), unique=True, nullable=False
    )
    originalFilename: Mapped[str] = mapped_column(
        "original_filename", String(255), nullable=False
    )
    declaredMimeType: Mapped[str] = mapped_column(
        "declared_mime_type", String(120), nullable=False
    )
    detectedMimeType: Mapped[str] = mapped_column(
        "detected_mime_type", String(120), nullable=False
    )
    sizeBytes: Mapped[int] = mapped_column("size_bytes", Integer, nullable=False)
    sha256Checksum: Mapped[str] = mapped_column(
        "sha256_checksum", String(64), nullable=False, index=True
    )
    scanStatus: Mapped[str] = mapped_column(
        "scan_status", String(32), nullable=False, default=ScanStatus.PENDING.value, index=True
    )
    metadataExtractionStatus: Mapped[str] = mapped_column(
        "metadata_extraction_status",
        String(32),
        nullable=False,
        default=MetadataExtractionStatus.PENDING.value,
    )
    extractedMetadata: Mapped[dict[str, Any] | None] = mapped_column(
        "extracted_metadata", JSON, nullable=True
    )
    accessClass: Mapped[str] = mapped_column(
        "access_class", String(32), nullable=False, default=AccessClass.RESTRICTED.value
    )
    uploadedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "uploaded_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    receivedAt: Mapped[datetime] = mapped_column(
        "received_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class AssetDerivative(Base, UUIDPrimaryKeyMixin):
    """Derived preview or thumbnail stored separately from untouched original evidence."""

    __tablename__ = "asset_derivatives"

    parentAssetId: Mapped[uuid.UUID] = mapped_column(
        "parent_asset_id",
        Uuid(as_uuid=True),
        ForeignKey("evidence_assets.id"),
        nullable=False,
        index=True,
    )
    derivativeType: Mapped[str] = mapped_column("derivative_type", String(64), nullable=False)
    storageKey: Mapped[str] = mapped_column(
        "storage_key", String(255), unique=True, nullable=False
    )
    mimeType: Mapped[str] = mapped_column("mime_type", String(120), nullable=False)
    sizeBytes: Mapped[int] = mapped_column("size_bytes", Integer, nullable=False)
    sha256Checksum: Mapped[str] = mapped_column("sha256_checksum", String(64), nullable=False)
    exifStripped: Mapped[bool] = mapped_column(
        "exif_stripped", Boolean, nullable=False, default=True
    )
    accessClass: Mapped[str] = mapped_column(
        "access_class", String(32), nullable=False, default=AccessClass.INTERNAL.value
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
