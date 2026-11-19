"""Pydantic schemas for evidence assets, derivatives, and scan status."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.evidence.models import (
    DerivativeType,
    MetadataExtractionStatus,
    ScanStatus,
)
from ecowatch.modules.observations.models import AccessClass


class AssetDerivativeResponse(CamelModel):
    """Serialized EXIF-stripped derivative or thumbnail record."""

    id: uuid.UUID
    parentAssetId: uuid.UUID
    derivativeType: DerivativeType
    mimeType: str
    sizeBytes: int
    sha256Checksum: str
    exifStripped: bool
    accessClass: AccessClass
    createdAt: datetime


class EvidenceAssetResponse(CamelModel):
    """Durable upload receipt and evidence asset metadata (storageKey omitted)."""

    id: uuid.UUID
    observationId: uuid.UUID
    organisationId: uuid.UUID
    originalFilename: str
    declaredMimeType: str
    detectedMimeType: str
    sizeBytes: int
    sha256Checksum: str
    scanStatus: ScanStatus
    metadataExtractionStatus: MetadataExtractionStatus
    accessClass: AccessClass
    receivedAt: datetime
    createdAt: datetime
    derivatives: list[AssetDerivativeResponse] = Field(default_factory=list)
    idempotentReplay: bool = False


class EvidenceScanStatusResponse(CamelModel):
    """Security scan and metadata extraction status for an evidence asset."""

    id: uuid.UUID
    observationId: uuid.UUID
    organisationId: uuid.UUID
    scanStatus: ScanStatus
    metadataExtractionStatus: MetadataExtractionStatus
    extractedMetadata: dict[str, Any] | None = None
    derivatives: list[AssetDerivativeResponse] = Field(default_factory=list)
