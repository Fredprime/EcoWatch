"""Local structural hardening of the evidence scan (no external scanner)."""

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

import ecowatch.modules.evidence.rules as evidenceRules
from ecowatch.core.spatial import format_point_wkt
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.evidence.models import (
    AccessClass,
    EvidenceAsset,
    MetadataExtractionStatus,
    ScanStatus,
)
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.observations.models import Observation
from tests.conftest import create_temp_org, make_jpeg_with_exif_bytes

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)


def _make_asset(
    dbSession: Session, storageProvider: StorageProvider, data: bytes
) -> EvidenceAsset:
    org = create_temp_org(dbSession)
    obs = Observation(
        organisationId=org.id,
        idempotencyKey=uuid.uuid4(),
        payloadHash="0" * 64,
        observationType="water_pollution",
        sourceType="community_anonymous",
        description="turbidity near the weir",
        observedAt=NOW,
        receivedAt=NOW,
        timePrecision="exact",
        location=format_point_wkt(-1.6244, 6.6885),
        locationPrecision="exact",
        qualityFlags=[],
        accessClass="internal",
        currentVersion=1,
        submittedByUserId=None,
    )
    dbSession.add(obs)
    dbSession.flush()
    key = f"originals/{uuid.uuid4().hex}"
    storageProvider.put_bytes(key, data)
    asset = EvidenceAsset(
        observationId=obs.id,
        organisationId=org.id,
        storageKey=key,
        originalFilename="sample.jpg",
        declaredMimeType="image/jpeg",
        detectedMimeType="image/jpeg",
        sizeBytes=len(data),
        sha256Checksum=hashlib.sha256(data).hexdigest(),
        scanStatus=ScanStatus.PENDING.value,
        metadataExtractionStatus=MetadataExtractionStatus.PENDING.value,
        extractedMetadata=None,
        accessClass=AccessClass.RESTRICTED.value,
        receivedAt=NOW,
        createdAt=NOW,
    )
    dbSession.add(asset)
    dbSession.commit()
    return asset


def test_image_dimension_rule_denies_oversized_and_allows_unknown() -> None:
    allowed, reason = evidenceRules.image_dimensions_within_bounds(
        {"width": 32, "height": 32}
    )
    assert allowed is True
    assert reason is None

    allowed, reason = evidenceRules.image_dimensions_within_bounds(None)
    assert allowed is True
    assert reason is None

    allowed, reason = evidenceRules.image_dimensions_within_bounds(
        {"width": 20_000, "height": 20_000}
    )
    assert allowed is False
    assert reason and "exceed local structural bounds" in reason


def test_scan_quarantines_image_over_local_dimension_bounds(
    dbSession: Session, storageProvider: StorageProvider, monkeypatch: object
) -> None:
    monkeypatch.setattr(evidenceRules, "MAX_IMAGE_WIDTH", 16)  # type: ignore[attr-defined]
    asset = _make_asset(dbSession, storageProvider, make_jpeg_with_exif_bytes())

    EvidenceService(dbSession, storageProvider).process_scan_and_derive(asset.id)

    dbSession.expire_all()
    refreshed = dbSession.get(EvidenceAsset, asset.id)
    assert refreshed is not None
    assert refreshed.scanStatus == ScanStatus.QUARANTINED.value
    assert refreshed.metadataExtractionStatus == MetadataExtractionStatus.EXTRACTED.value
    assert refreshed.extractedMetadata and refreshed.extractedMetadata["width"] == 32

    audit = dbSession.scalar(
        select(AuditEvent).where(
            AuditEvent.action == "evidence.scanned",
            AuditEvent.targetId == asset.id,
        )
    )
    assert audit is not None
    assert audit.reason and "exceed local structural bounds" in audit.reason
