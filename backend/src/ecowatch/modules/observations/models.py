"""SQLAlchemy ORM models for observations, versions, sources, methods, and units."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from ecowatch.core.spatial import GeographyType


class SourceType(StrEnum):
    """Canonical observation source classifications."""

    COMMUNITY_ANONYMOUS = "community_anonymous"
    COMMUNITY_REGISTERED = "community_registered"
    FIELD_TEAM = "field_team"
    SENSOR = "sensor"
    LABORATORY = "laboratory"
    REMOTE_SENSING = "remote_sensing"
    INSTITUTIONAL_RECORD = "institutional_record"
    RESEARCH = "research"


class TimePrecision(StrEnum):
    """Precision classification for reported observation timestamps."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    RANGE = "range"
    UNKNOWN = "unknown"


class LocationPrecision(StrEnum):
    """Precision classification for observation coordinates."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    AREA = "area"
    UNKNOWN = "unknown"


class AccessClass(StrEnum):
    """Sensitivity and access classification for observations and evidence."""

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    HIGH_SENSITIVITY = "high_sensitivity"


class Method(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Standardised field, laboratory, or analytical method definition."""

    __tablename__ = "methods"

    code: Mapped[str] = mapped_column("code", String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    version: Mapped[str] = mapped_column("version", String(64), nullable=False)
    protocolText: Mapped[str | None] = mapped_column("protocol_text", Text, nullable=True)
    instrumentClass: Mapped[str | None] = mapped_column(
        "instrument_class", String(120), nullable=True
    )


class Unit(Base, UUIDPrimaryKeyMixin):
    """Controlled measurement unit vocabulary."""

    __tablename__ = "units"

    symbol: Mapped[str] = mapped_column("symbol", String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column("name", String(120), nullable=False)
    dimension: Mapped[str] = mapped_column("dimension", String(64), nullable=False)
    ucumCode: Mapped[str | None] = mapped_column("ucum_code", String(64), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class Observation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Environmental observation aggregate with strict provenance and tenant scoping."""

    __tablename__ = "observations"

    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    idempotencyKey: Mapped[uuid.UUID] = mapped_column(
        "idempotency_key", Uuid(as_uuid=True), unique=True, nullable=False
    )
    payloadHash: Mapped[str] = mapped_column("payload_hash", String(64), nullable=False)
    trackingCodeHash: Mapped[str | None] = mapped_column(
        "tracking_code_hash", String(64), nullable=True, index=True
    )
    observationType: Mapped[str] = mapped_column(
        "observation_type", String(100), nullable=False, index=True
    )
    sourceType: Mapped[str] = mapped_column(
        "source_type", String(64), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column("description", Text, nullable=False)
    isFirsthand: Mapped[bool | None] = mapped_column("is_firsthand", Boolean, nullable=True)
    structuredData: Mapped[dict[str, Any] | None] = mapped_column(
        "structured_data", JSON, nullable=True
    )
    methodId: Mapped[uuid.UUID | None] = mapped_column(
        "method_id", Uuid(as_uuid=True), ForeignKey("methods.id"), nullable=True, index=True
    )
    unitId: Mapped[uuid.UUID | None] = mapped_column(
        "unit_id", Uuid(as_uuid=True), ForeignKey("units.id"), nullable=True, index=True
    )
    instrument: Mapped[str | None] = mapped_column("instrument", String(120), nullable=True)
    eventStartAt: Mapped[datetime | None] = mapped_column(
        "event_start_at", DateTime(timezone=True), nullable=True
    )
    observedAt: Mapped[datetime | None] = mapped_column(
        "observed_at", DateTime(timezone=True), nullable=True, index=True
    )
    observedEndAt: Mapped[datetime | None] = mapped_column(
        "observed_end_at", DateTime(timezone=True), nullable=True
    )
    submittedAt: Mapped[datetime | None] = mapped_column(
        "submitted_at", DateTime(timezone=True), nullable=True
    )
    receivedAt: Mapped[datetime] = mapped_column(
        "received_at", DateTime(timezone=True), nullable=False, index=True
    )
    timePrecision: Mapped[str] = mapped_column("time_precision", String(32), nullable=False)
    originalTimeWording: Mapped[str | None] = mapped_column(
        "original_time_wording", String(200), nullable=True
    )
    location: Mapped[str | None] = mapped_column(
        "location", GeographyType("POINT", 4326), nullable=True
    )
    publicLocation: Mapped[str | None] = mapped_column(
        "public_location", GeographyType("POINT", 4326), nullable=True
    )
    locationPrecision: Mapped[str] = mapped_column(
        "location_precision", String(32), nullable=False
    )
    originalLocationWording: Mapped[str | None] = mapped_column(
        "original_location_wording", String(200), nullable=True
    )
    qualityFlags: Mapped[list[str]] = mapped_column(
        "quality_flags", JSON, nullable=False, default=list
    )
    accessClass: Mapped[str] = mapped_column(
        "access_class", String(32), nullable=False, default=AccessClass.RESTRICTED.value
    )
    isHidden: Mapped[bool] = mapped_column("is_hidden", Boolean, nullable=False, default=False)
    currentVersion: Mapped[int] = mapped_column(
        "current_version", Integer, nullable=False, default=1
    )
    submittedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "submitted_by_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )


class ObservationVersion(Base, UUIDPrimaryKeyMixin):
    """Append-only version history capturing observation corrections without mutation."""

    __tablename__ = "observation_versions"
    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "version_number",
            name="uq_observation_versions_obs_version",
        ),
    )

    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        nullable=False,
        index=True,
    )
    versionNumber: Mapped[int] = mapped_column("version_number", Integer, nullable=False)
    changedFields: Mapped[dict[str, Any]] = mapped_column(
        "changed_fields", JSON, nullable=False
    )
    reason: Mapped[str] = mapped_column("reason", Text, nullable=False)
    editedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        "edited_by_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )


class ObservationSource(Base, UUIDPrimaryKeyMixin):
    """Strictly isolated contributor identity, contact, and consent metadata."""

    __tablename__ = "observation_sources"

    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id",
        Uuid(as_uuid=True),
        ForeignKey("observations.id"),
        unique=True,
        nullable=False,
    )
    reporterName: Mapped[str | None] = mapped_column(
        "reporter_name", String(200), nullable=True
    )
    contactChannel: Mapped[str | None] = mapped_column(
        "contact_channel", String(64), nullable=True
    )
    contactValue: Mapped[str | None] = mapped_column(
        "contact_value", String(255), nullable=True
    )
    consentGiven: Mapped[bool] = mapped_column(
        "consent_given", Boolean, nullable=False, default=False
    )
    privacyNoticeVersion: Mapped[str] = mapped_column(
        "privacy_notice_version", String(64), nullable=False
    )
    safetyAck: Mapped[bool] = mapped_column(
        "safety_ack", Boolean, nullable=False, default=False
    )
    clientMetadata: Mapped[dict[str, Any] | None] = mapped_column(
        "client_metadata", JSON, nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
