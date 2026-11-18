"""Pydantic schemas for observation intake and anonymous receipt lookup."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.observations.models import (
    AccessClass,
    LocationPrecision,
    SourceType,
    TimePrecision,
)
from ecowatch.modules.observations.schemas import normalize_utc


class ObservationSourceInput(CamelModel):
    """Contributor contact, consent, and client metadata stored strictly in observation_sources."""

    reporterName: str | None = Field(default=None, max_length=200)
    contactChannel: str | None = Field(default=None, max_length=64)
    contactValue: str | None = Field(default=None, max_length=255)
    consentGiven: bool = False
    privacyNoticeVersion: str = Field(default="v1", min_length=1, max_length=64)
    safetyAck: bool = False
    clientMetadata: dict[str, Any] | None = None


class CreateObservationRequest(CamelModel):
    """Idempotent observation intake payload for anonymous and authenticated submitters."""

    idempotencyKey: uuid.UUID
    organisationId: uuid.UUID | None = None
    observationType: str = Field(min_length=1, max_length=100)
    sourceType: SourceType | None = None
    description: str = Field(min_length=1, max_length=10_000)
    isFirsthand: bool | None = None
    structuredData: dict[str, Any] | None = None
    methodId: uuid.UUID | None = None
    unitId: uuid.UUID | None = None
    instrument: str | None = Field(default=None, max_length=120)
    eventStartAt: datetime | None = None
    observedAt: datetime | None = None
    observedEndAt: datetime | None = None
    submittedAt: datetime | None = None
    timePrecision: TimePrecision = TimePrecision.UNKNOWN
    originalTimeWording: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    locationPrecision: LocationPrecision = LocationPrecision.UNKNOWN
    originalLocationWording: str | None = Field(default=None, max_length=200)
    accessClass: AccessClass = AccessClass.RESTRICTED
    source: ObservationSourceInput | None = None

    @model_validator(mode="after")
    def validate_intake_constraints(self) -> CreateObservationRequest:
        if not self.observationType.strip():
            raise ValueError("observationType must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")
        if (self.lat is None) != (self.lon is None):
            raise ValueError("Both lat and lon must be provided together")
        obsAt = normalize_utc(self.observedAt)
        obsEnd = normalize_utc(self.observedEndAt)
        if obsEnd is not None and obsAt is None:
            raise ValueError("observedEndAt requires observedAt")
        if obsAt is not None and obsEnd is not None and obsEnd < obsAt:
            raise ValueError("observedEndAt must be greater than or equal to observedAt")
        return self


class IntakeReceiptResponse(CamelModel):
    """Durable intake receipt returned immediately after persistence."""

    observationId: uuid.UUID
    organisationId: uuid.UUID
    receivedAt: datetime
    observationType: str
    timePrecision: TimePrecision
    locationPrecision: LocationPrecision
    currentVersion: int
    trackingCode: str | None = None
    idempotentReplay: bool = False


class ReceiptLookupRequest(CamelModel):
    """Unauthenticated tracking-code receipt lookup request."""

    trackingCode: str = Field(min_length=1, max_length=256)


class ReceiptLookupResponse(CamelModel):
    """Minimal receipt response exposing zero PII or other observations."""

    observationId: uuid.UUID
    receivedAt: datetime
    observationType: str
    timePrecision: TimePrecision
    locationPrecision: LocationPrecision
    evidenceCount: int
