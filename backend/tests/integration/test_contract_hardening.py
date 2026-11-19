"""ADR-036: permanent/transient error taxonomy, Retry-After, idempotent media upload."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.errors import ErrorCode, classify_error
from ecowatch.core.schemas import ErrorCategory
from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.spatial import format_point_wkt
from ecowatch.modules.evidence.models import EvidenceAsset
from ecowatch.modules.identity.permissions import Role
from ecowatch.modules.observations.models import Observation
from tests.conftest import (
    auth_headers,
    create_temp_org,
    create_temp_user,
    make_jpeg_with_exif_bytes,
)


def test_classify_error_distinguishes_permanent_and_transient() -> None:
    assert classify_error(ErrorCode.NOT_FOUND, 404) == ErrorCategory.PERMANENT
    assert classify_error(ErrorCode.VALIDATION_ERROR, 422) == ErrorCategory.PERMANENT
    assert classify_error(ErrorCode.RATE_LIMIT_EXCEEDED, 429) == ErrorCategory.TRANSIENT
    assert classify_error(ErrorCode.INTERNAL_ERROR, 500) == ErrorCategory.TRANSIENT
    assert classify_error(ErrorCode.EVIDENCE_NOT_READY, 409) == ErrorCategory.TRANSIENT
    assert classify_error(ErrorCode.CONFLICT, 409) == ErrorCategory.PERMANENT


def test_receipt_lockout_sends_retry_after_and_transient_category(
    client: TestClient, dbSession: Session
) -> None:
    org = create_temp_org(dbSession)
    intake = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "water_turbidity",
            "description": "Sediment plume",
            "observedAt": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "timePrecision": "approximate",
            "lat": 6.6885,
            "lon": -1.6244,
            "locationPrecision": "approximate",
            "source": {
                "reporterName": "Tester",
                "contactChannel": "phone",
                "contactValue": "+233200000000",
                "consentGiven": True,
                "privacyNoticeVersion": "v1",
                "safetyAck": True,
            },
        },
    )
    assert intake.status_code == 201

    for _ in range(3):
        assert (
            client.post(
                "/api/v1/observations/receipt-lookup",
                json={"trackingCode": "wrong-code"},
            ).status_code
            == 404
        )

    locked = client.post(
        "/api/v1/observations/receipt-lookup",
        json={"trackingCode": "wrong-code"},
    )
    assert locked.status_code == 429
    assert locked.json()["code"] == "TRACKING_CODE_LOCKED"
    assert locked.json()["category"] == "transient"
    assert locked.json()["retryAfterSeconds"] > 0
    assert locked.headers["Retry-After"] == str(locked.json()["retryAfterSeconds"])

    # A malformed public intake request is a permanent failure and never
    # carries a Retry-After hint.
    permanent = client.post("/api/v1/observations", json={})
    assert permanent.status_code == 422
    assert permanent.json()["category"] == "permanent"
    assert "Retry-After" not in permanent.headers


def test_media_upload_replay_is_idempotent(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    contributor = create_temp_user(dbSession, memberships=[(org.id, Role.REGISTERED_CONTRIBUTOR)])
    obs = Observation(
        organisationId=org.id,
        idempotencyKey=uuid.uuid4(),
        payloadHash="0" * 64,
        observationType="water_pollution",
        sourceType="community_registered",
        description="turbidity near the weir",
        observedAt=datetime.now(UTC) - timedelta(hours=2),
        receivedAt=datetime.now(UTC),
        timePrecision="exact",
        location=format_point_wkt(-1.6244, 6.6885),
        locationPrecision="exact",
        qualityFlags=[],
        accessClass="internal",
        currentVersion=1,
    )
    dbSession.add(obs)
    dbSession.commit()

    headers = auth_headers(authProvider, contributor)
    key = str(uuid.uuid4())
    url = f"/api/v1/observations/{obs.id}/evidence"
    jpegBytes = make_jpeg_with_exif_bytes()

    def upload(idempotencyKey: str, data: bytes):
        return client.post(
            url,
            files={"file": ("sample.jpg", data, "image/jpeg")},
            headers={**headers, "Idempotency-Key": idempotencyKey},
        )

    first = upload(key, jpegBytes)
    assert first.status_code == 201
    assert first.json()["idempotentReplay"] is False
    assetId = first.json()["id"]

    replay = upload(key, jpegBytes)
    assert replay.status_code == 201
    assert replay.json()["id"] == assetId
    assert replay.json()["idempotentReplay"] is True

    count = len(dbSession.scalars(select(EvidenceAsset)).all())
    assert count == 1

    other = upload(str(uuid.uuid4()), jpegBytes)
    assert other.status_code == 201
    assert other.json()["id"] != assetId

    conflict = upload(key, make_jpeg_with_exif_bytes() + b"different-content")
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_KEY_CONFLICT"
