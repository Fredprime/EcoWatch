"""Pydantic boundary schemas for the environmental data catalogue."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.core.spatial import validate_wkt_geometry


def _required(value: str) -> str:
    """Trim and reject blank required text."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Value must not be blank")
    return cleaned


def _geometry_text(value: Any) -> str | None:
    """Normalise a stored geometry value to WKT text."""
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


class CreateDatasetRequest(CamelModel):
    """Rights-recorded dataset creation payload."""

    organisationId: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=200)
    licence: str = Field(min_length=1, max_length=200)
    attribution: str = Field(min_length=1, max_length=2000)
    permittedUse: str = Field(min_length=1, max_length=2000)
    crs: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=10000)
    coverageStartAt: datetime | None = None
    coverageEndAt: datetime | None = None
    coverageGeometry: str | None = Field(default=None, max_length=50000)

    @field_validator("name", "owner", "licence", "attribution", "permittedUse", "crs")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)

    @field_validator("coverageGeometry", mode="before")
    @classmethod
    def validate_coverage_geometry(cls, value: Any) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return validate_wkt_geometry(str(value))


class AddDatasetVersionRequest(CamelModel):
    """Immutable provenance snapshot appended to an existing dataset."""

    organisationId: uuid.UUID
    versionLabel: str = Field(min_length=1, max_length=100)
    sourceAcquisitionAt: datetime
    resolution: str = Field(min_length=1, max_length=100)
    crs: str = Field(min_length=1, max_length=50)
    method: str = Field(min_length=1, max_length=10000)
    licence: str = Field(min_length=1, max_length=200)
    attribution: str = Field(min_length=1, max_length=2000)
    permittedUse: str = Field(min_length=1, max_length=2000)
    limitations: str | None = Field(default=None, max_length=10000)
    qualityNotes: str | None = Field(default=None, max_length=10000)
    checksum: str | None = Field(default=None, max_length=128)
    storageKey: str | None = Field(default=None, max_length=500)

    @field_validator(
        "versionLabel", "resolution", "crs", "method", "licence", "attribution", "permittedUse"
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class DatasetResponse(CamelModel):
    """Catalogue dataset with its recorded rights and coverage."""

    id: uuid.UUID
    organisationId: uuid.UUID
    name: str
    description: str | None = None
    owner: str
    licence: str
    attribution: str
    permittedUse: str
    crs: str
    coverageStartAt: datetime | None = None
    coverageEndAt: datetime | None = None
    coverageGeometry: str | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_validator("coverageGeometry", mode="before")
    @classmethod
    def serialize_geometry(cls, value: Any) -> str | None:
        return _geometry_text(value)


class DatasetVersionResponse(CamelModel):
    """Complete, immutable provenance snapshot for one dataset version."""

    id: uuid.UUID
    datasetId: uuid.UUID
    versionLabel: str
    sourceAcquisitionAt: datetime
    resolution: str
    crs: str
    method: str
    limitations: str | None = None
    qualityNotes: str | None = None
    licenceSnapshot: str
    attributionSnapshot: str
    permittedUseSnapshot: str
    checksum: str | None = None
    storageKey: str | None = None
    createdAt: datetime
