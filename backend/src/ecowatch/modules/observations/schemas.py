"""Pydantic boundary schemas and geo-serialization helpers for observations."""

import uuid
from datetime import UTC, datetime
from typing import Any, Self

from pydantic import Field, model_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.core.spatial import coarsen_point_wkt, format_point_wkt, parse_point_wkt
from ecowatch.modules.observations.models import (
    AccessClass,
    LocationPrecision,
    Observation,
    SourceType,
    TimePrecision,
)


def normalize_utc(value: datetime | None) -> datetime | None:
    """Normalize an optional datetime to timezone-aware UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class GeoPointSchema(CamelModel):
    """WGS84 geographic coordinate pair."""

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


def coarsen_point(
    lon: float,
    lat: float,
    *,
    accessClass: AccessClass,
    locationPrecision: LocationPrecision,
) -> str | None:
    """Return public-safe WKT point according to sensitivity and precision rules."""
    if accessClass == AccessClass.HIGH_SENSITIVITY:
        return None
    if accessClass == AccessClass.PUBLIC and locationPrecision == LocationPrecision.EXACT:
        return format_point_wkt(lon, lat)
    return coarsen_point_wkt(lon, lat)


def parse_point(rawValue: Any) -> GeoPointSchema | None:
    """Convert stored WKT POINT value into a GeoPointSchema."""
    coords = parse_point_wkt(rawValue)
    if coords is None:
        return None
    lon, lat = coords
    return GeoPointSchema(lat=lat, lon=lon)


class ObservationPublicSummaryResponse(CamelModel):
    """Public/redacted observation projection without contributor identity or exact coordinates."""

    id: uuid.UUID
    organisationId: uuid.UUID
    observationType: str
    sourceType: SourceType
    description: str
    isFirsthand: bool | None = None
    structuredData: dict[str, Any] | None = None
    methodId: uuid.UUID | None = None
    unitId: uuid.UUID | None = None
    instrument: str | None = None
    eventStartAt: datetime | None = None
    observedAt: datetime | None = None
    observedEndAt: datetime | None = None
    submittedAt: datetime | None = None
    receivedAt: datetime
    timePrecision: TimePrecision
    originalTimeWording: str | None = None
    publicLocation: GeoPointSchema | None = None
    locationPrecision: LocationPrecision
    qualityFlags: list[str]
    accessClass: AccessClass
    isHidden: bool
    currentVersion: int
    createdAt: datetime
    updatedAt: datetime

    @classmethod
    def from_orm_record(cls, obs: Observation) -> Self:
        """Map an Observation ORM row into a redacted DTO."""
        return cls(
            id=obs.id,
            organisationId=obs.organisationId,
            observationType=obs.observationType,
            sourceType=SourceType(obs.sourceType),
            description=obs.description,
            isFirsthand=obs.isFirsthand,
            structuredData=obs.structuredData,
            methodId=obs.methodId,
            unitId=obs.unitId,
            instrument=obs.instrument,
            eventStartAt=obs.eventStartAt,
            observedAt=obs.observedAt,
            observedEndAt=obs.observedEndAt,
            submittedAt=obs.submittedAt,
            receivedAt=obs.receivedAt,
            timePrecision=TimePrecision(obs.timePrecision),
            originalTimeWording=obs.originalTimeWording,
            publicLocation=parse_point(obs.publicLocation),
            locationPrecision=LocationPrecision(obs.locationPrecision),
            qualityFlags=list(obs.qualityFlags or []),
            accessClass=AccessClass(obs.accessClass),
            isHidden=obs.isHidden,
            currentVersion=obs.currentVersion,
            createdAt=obs.createdAt,
            updatedAt=obs.updatedAt,
        )


class ObservationRestrictedResponse(ObservationPublicSummaryResponse):
    """Restricted staff/owner view with exact coordinates and raw location wording."""

    location: GeoPointSchema | None = None
    originalLocationWording: str | None = None
    submittedByUserId: uuid.UUID | None = None

    @classmethod
    def from_orm_record(cls, obs: Observation) -> Self:
        """Map an Observation ORM row into a restricted DTO."""
        base = ObservationPublicSummaryResponse.from_orm_record(obs)
        return cls(
            **base.model_dump(),
            location=parse_point(obs.location),
            originalLocationWording=obs.originalLocationWording,
            submittedByUserId=obs.submittedByUserId,
        )


class ObservationVersionResponse(CamelModel):
    """Serialized append-only observation version record."""

    id: uuid.UUID
    observationId: uuid.UUID
    versionNumber: int
    changedFields: dict[str, Any]
    reason: str
    editedByUserId: uuid.UUID | None = None
    createdAt: datetime


class CreateCorrectionRequest(CamelModel):
    """Controlled correction request appending a new observation version."""

    reason: str = Field(min_length=1, max_length=2000)
    observationType: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    isFirsthand: bool | None = None
    structuredData: dict[str, Any] | None = None
    methodId: uuid.UUID | None = None
    unitId: uuid.UUID | None = None
    instrument: str | None = Field(default=None, max_length=120)
    eventStartAt: datetime | None = None
    observedAt: datetime | None = None
    observedEndAt: datetime | None = None
    timePrecision: TimePrecision | None = None
    originalTimeWording: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    locationPrecision: LocationPrecision | None = None
    originalLocationWording: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_correction(self) -> Self:
        if (self.lat is None) != (self.lon is None):
            raise ValueError("Both lat and lon must be provided together")
        if self.description is not None and not self.description.strip():
            raise ValueError("description must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        data = self.model_dump(exclude={"reason"}, exclude_unset=True)
        if not data:
            raise ValueError("At least one field must be provided for correction")
        return self


class UpdateQualityFlagsRequest(CamelModel):
    """Request payload to set observation quality flags."""

    qualityFlags: list[str] = Field(max_length=50)
    reason: str | None = Field(default=None, max_length=1000)


class ObservationSourceResponse(CamelModel):
    """Restricted contributor identity/contact record (OA own org / SA only)."""

    id: uuid.UUID
    observationId: uuid.UUID
    reporterName: str | None = None
    contactChannel: str | None = None
    contactValue: str | None = None
    consentGiven: bool
    privacyNoticeVersion: str
    safetyAck: bool
    clientMetadata: dict[str, Any] | None = None
    createdAt: datetime


class CreateMethodRequest(CamelModel):
    """Request payload to register a measurement/field method."""

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=64)
    protocolText: str | None = None
    instrumentClass: str | None = Field(default=None, max_length=120)


class MethodResponse(CamelModel):
    """Serialized method record."""

    id: uuid.UUID
    code: str
    name: str
    version: str
    protocolText: str | None = None
    instrumentClass: str | None = None
    createdAt: datetime
    updatedAt: datetime


class CreateUnitRequest(CamelModel):
    """Request payload to register a controlled measurement unit."""

    symbol: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    dimension: str = Field(min_length=1, max_length=64)
    ucumCode: str | None = Field(default=None, max_length=64)


class UnitResponse(CamelModel):
    """Serialized unit record."""

    id: uuid.UUID
    symbol: str
    name: str
    dimension: str
    ucumCode: str | None = None
    createdAt: datetime
