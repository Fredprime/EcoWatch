"""End-to-end Phase 1 API workflow integration tests (using temporary isolated records)."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.evidence.models import AssetDerivative, EvidenceAsset, ScanStatus
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.identity.permissions import Principal, Role, SystemRole
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.jobs.worker import run_once
from ecowatch.modules.observations.models import AccessClass
from tests.conftest import (
    auth_headers,
    create_temp_org,
    create_temp_user,
    make_jpeg_with_exif_bytes,
)


def test_health_and_request_id_header(client: TestClient) -> None:
    resp = client.get("/health", headers={"X-Request-ID": "req-phase1-check"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-phase1-check"
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["storageRootReady"] is True


def test_identity_org_membership_and_audit(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    sysAdmin = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    saHeaders = auth_headers(authProvider, sysAdmin)

    orgResp = client.post(
        "/api/v1/organisations",
        json={"name": "Volta Basin Watch", "orgType": "ngo"},
        headers=saHeaders,
    )
    assert orgResp.status_code == 201
    orgId = orgResp.json()["id"]

    userResp = client.post(
        "/api/v1/users",
        json={
            "email": "field.lead@example.test",
            "displayName": "Field Lead",
            "password": "StrongPassword123",
        },
        headers=saHeaders,
    )
    assert userResp.status_code == 201
    userId = userResp.json()["id"]
    assert "passwordHash" not in userResp.json()

    memberResp = client.post(
        f"/api/v1/organisations/{orgId}/memberships",
        json={"userId": userId, "role": "investigator", "reason": "Assigned lead"},
        headers=saHeaders,
    )
    assert memberResp.status_code == 201
    assert memberResp.json()["role"] == "investigator"

    loginResp = client.post(
        "/api/v1/auth/login",
        json={"email": "field.lead@example.test", "password": "StrongPassword123"},
    )
    assert loginResp.status_code == 200
    token = loginResp.json()["accessToken"]

    meResp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert meResp.status_code == 200
    assert len(meResp.json()["memberships"]) == 1

    auditResp = client.get("/api/v1/audit/events?action=role.changed", headers=saHeaders)
    assert auditResp.status_code == 200
    assert len(auditResp.json()["items"]) == 1


def test_anonymous_intake_idempotency_conflict_and_lockout(
    client: TestClient,
    dbSession: Session,
) -> None:
    org = create_temp_org(dbSession)
    idempotencyKey = str(uuid.uuid4())
    observedAt = (datetime.now(UTC) - timedelta(hours=2)).isoformat()

    payload = {
        "idempotencyKey": idempotencyKey,
        "organisationId": str(org.id),
        "observationType": "water_turbidity",
        "description": "Muddy sediment plume downstream of bend",
        "observedAt": observedAt,
        "timePrecision": "approximate",
        "lat": 6.6885,
        "lon": -1.6244,
        "locationPrecision": "approximate",
        "source": {
            "reporterName": "Ama Boateng",
            "contactChannel": "phone",
            "contactValue": "+233200000000",
            "consentGiven": True,
            "privacyNoticeVersion": "v1",
            "safetyAck": True,
        },
    }
    firstResp = client.post("/api/v1/observations", json=payload)
    assert firstResp.status_code == 201
    firstBody = firstResp.json()
    trackingCode = firstBody["trackingCode"]
    assert trackingCode is not None
    assert firstBody["idempotentReplay"] is False

    replayResp = client.post("/api/v1/observations", json=payload)
    assert replayResp.status_code == 200
    replayBody = replayResp.json()
    assert replayBody["observationId"] == firstBody["observationId"]
    assert replayBody["trackingCode"] is None
    assert replayBody["idempotentReplay"] is True

    conflictPayload = {**payload, "description": "Altered payload with same key"}
    conflictResp = client.post("/api/v1/observations", json=conflictPayload)
    assert conflictResp.status_code == 409
    assert conflictResp.json()["code"] == "IDEMPOTENCY_KEY_CONFLICT"

    lookupOk = client.post(
        "/api/v1/observations/receipt-lookup",
        json={"trackingCode": trackingCode},
    )
    assert lookupOk.status_code == 200
    assert lookupOk.json()["observationId"] == firstBody["observationId"]
    assert "reporterName" not in lookupOk.json()

    for _ in range(3):
        badLookup = client.post(
            "/api/v1/observations/receipt-lookup",
            json={"trackingCode": "wrong-code-attempt"},
        )
        assert badLookup.status_code == 404

    lockedResp = client.post(
        "/api/v1/observations/receipt-lookup",
        json={"trackingCode": trackingCode},
    )
    assert lockedResp.status_code == 429
    assert lockedResp.json()["code"] == "TRACKING_CODE_LOCKED"


def test_registered_observation_versions_clarifications_and_evidence_worker(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: LocalFilesystemStorage,
    testSettings: Settings,
) -> None:
    org = create_temp_org(dbSession)
    contributor = create_temp_user(
        dbSession, memberships=[(org.id, Role.REGISTERED_CONTRIBUTOR)]
    )
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    specialist = create_temp_user(dbSession, memberships=[(org.id, Role.ENVIRONMENTAL_SPECIALIST)])

    specHeaders = auth_headers(authProvider, specialist)
    contribHeaders = auth_headers(authProvider, contributor)
    revHeaders = auth_headers(authProvider, reviewer)

    methodResp = client.post(
        "/api/v1/methods",
        json={"code": "WQ_NTU", "name": "Portable Turbidimeter", "version": "1.0"},
        headers=specHeaders,
    )
    assert methodResp.status_code == 201
    unitResp = client.post(
        "/api/v1/units",
        json={"symbol": "NTU", "name": "Nephelometric Turbidity Units", "dimension": "turbidity"},
        headers=specHeaders,
    )
    assert unitResp.status_code == 201

    obsResp = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "water_turbidity",
            "sourceType": "field_team",
            "description": "Measured 42 NTU at intake point",
            "methodId": methodResp.json()["id"],
            "unitId": unitResp.json()["id"],
            "structuredData": {"turbidity": 42},
            "lat": 6.5,
            "lon": -1.5,
            "locationPrecision": "exact",
            "timePrecision": "exact",
            "observedAt": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        },
        headers=contribHeaders,
    )
    assert obsResp.status_code == 201
    obsId = uuid.UUID(obsResp.json()["observationId"])

    corrOwn = client.post(
        f"/api/v1/observations/{obsId}/corrections",
        json={"description": "Measured 44 NTU after calibration check", "reason": "Typo fix"},
        headers=contribHeaders,
    )
    assert corrOwn.status_code == 201
    assert corrOwn.json()["currentVersion"] == 2
    versionsResp = client.get(f"/api/v1/observations/{obsId}/versions", headers=revHeaders)
    assert versionsResp.status_code == 200
    assert [v["versionNumber"] for v in versionsResp.json()] == [1, 2]

    flagResp = client.patch(
        f"/api/v1/observations/{obsId}/quality-flags",
        json={"qualityFlags": ["calibrated_field_reading"]},
        headers=revHeaders,
    )
    assert flagResp.status_code == 200

    blockedAfterReview = client.post(
        f"/api/v1/observations/{obsId}/corrections",
        json={"description": "Late edit", "reason": "Should fail after review"},
        headers=contribHeaders,
    )
    assert blockedAfterReview.status_code == 409

    clarResp = client.post(
        f"/api/v1/observations/{obsId}/clarifications",
        json={
            "recipientUserId": str(contributor.id),
            "message": "Please confirm river gauge distance",
        },
        headers=revHeaders,
    )
    assert clarResp.status_code == 201

    inboxResp = client.get("/api/v1/notifications?unreadOnly=true", headers=contribHeaders)
    assert inboxResp.status_code == 200
    assert len(inboxResp.json()["items"]) == 1
    notifId = inboxResp.json()["items"][0]["id"]
    markRead = client.post(f"/api/v1/notifications/{notifId}/read", headers=contribHeaders)
    assert markRead.status_code == 200
    assert markRead.json()["isRead"] is True

    jpegBytes = make_jpeg_with_exif_bytes()
    expectedSha = hashlib.sha256(jpegBytes).hexdigest()
    contribPrincipal = Principal(
        userId=contributor.id,
        memberships=((org.id, Role.REGISTERED_CONTRIBUTOR),),
        isAuthenticated=True,
    )
    asset = EvidenceService(dbSession, storageProvider).upload_evidence(
        contribPrincipal,
        obsId,
        rawBytes=jpegBytes,
        filename="river_sample.jpg",
        declaredMimeType="image/jpeg",
        accessClass=AccessClass.RESTRICTED,
        trackingCode=None,
        settings=testSettings,
        requestId="req-upload",
    )
    assert asset.scanStatus == ScanStatus.PENDING.value
    assert asset.sha256Checksum == expectedSha

    # Intake now also queues a correlation scan, so assert on the job this test
    # cares about rather than on how many jobs happen to be pending.
    processedCount = run_once(dbSession, storageProvider, maxAttempts=3)
    assert processedCount >= 1
    evidenceJob = dbSession.scalar(
        select(ProcessingJob).where(ProcessingJob.jobType == "evidence.scan_and_derive")
    )
    assert evidenceJob is not None
    assert evidenceJob.status == JobStatus.PROCESSED.value
    dbSession.expire_all()
    updatedAsset = dbSession.execute(
        select(EvidenceAsset).where(EvidenceAsset.id == asset.id)
    ).scalar_one()
    assert updatedAsset.scanStatus == ScanStatus.CLEAN.value
    assert storageProvider.get_bytes(updatedAsset.storageKey) == jpegBytes

    derivatives = (
        dbSession.execute(
            select(AssetDerivative).where(AssetDerivative.parentAssetId == asset.id)
        )
        .scalars()
        .all()
    )
    assert {d.derivativeType for d in derivatives} == {"exif_stripped_preview", "thumbnail"}
    for item in derivatives:
        assert item.exifStripped is True
        assert b"EcoCamera" not in storageProvider.get_bytes(item.storageKey)
    derivative = derivatives[0]

    origResp = client.get(f"/api/v1/evidence/{asset.id}/original", headers=specHeaders)
    assert origResp.status_code == 200
    assert origResp.content == jpegBytes

    derivResp = client.get(
        f"/api/v1/evidence/{asset.id}/derivatives/{derivative.id}",
        headers=revHeaders,
    )
    assert derivResp.status_code == 200
    assert b"EcoCamera" not in derivResp.content


def test_cases_many_to_many_status_transitions_timeline_and_public_summary(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    contributor = create_temp_user(
        dbSession, memberships=[(org.id, Role.REGISTERED_CONTRIBUTOR)]
    )
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    specialist = create_temp_user(dbSession, memberships=[(org.id, Role.ENVIRONMENTAL_SPECIALIST)])
    orgAdmin = create_temp_user(dbSession, memberships=[(org.id, Role.ORGANISATION_ADMIN)])

    obsResp = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "river_foam",
            "description": "Persistent white foam near culvert",
            "eventStartAt": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
            "observedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "submittedAt": (datetime.now(UTC) - timedelta(hours=3)).isoformat(),
            "timePrecision": "approximate",
        },
        headers=auth_headers(authProvider, contributor),
    )
    assert obsResp.status_code == 201
    obsId = obsResp.json()["observationId"]

    invHeaders = auth_headers(authProvider, investigator)
    specHeaders = auth_headers(authProvider, specialist)
    oaHeaders = auth_headers(authProvider, orgAdmin)

    caseOne = client.post(
        "/api/v1/cases",
        json={
            "organisationId": str(org.id),
            "title": "Culvert Foam Investigation",
            "summary": "Investigating reported river foam",
            "areaGeometry": "POLYGON((-1.63 6.68, -1.61 6.68, -1.61 6.70, -1.63 6.70, -1.63 6.68))",
            "publicGeometry": "POINT(-1.62 6.69)",
        },
        headers=invHeaders,
    )
    assert caseOne.status_code == 201
    caseOneId = caseOne.json()["id"]

    caseTwo = client.post(
        "/api/v1/cases",
        json={
            "organisationId": str(org.id),
            "title": "Downstream Catchment Review",
            "summary": "Secondary catchment monitoring",
        },
        headers=invHeaders,
    )
    assert caseTwo.status_code == 201
    caseTwoId = caseTwo.json()["id"]

    linkOne = client.post(
        f"/api/v1/cases/{caseOneId}/observations",
        json={"observationId": obsId, "linkRationale": "Direct upstream sighting"},
        headers=invHeaders,
    )
    linkTwo = client.post(
        f"/api/v1/cases/{caseTwoId}/observations",
        json={
            "observationId": obsId,
            "linkRationale": "Potentially relevant downstream indicator",
            "isContested": True,
            "contestedNote": "Could also reflect local detergent discharge",
        },
        headers=invHeaders,
    )
    assert linkOne.status_code == 201
    assert linkTwo.status_code == 201
    assert linkTwo.json()["reviewStatus"] == "contested"

    assert (
        client.post(
            f"/api/v1/cases/{caseOneId}/status",
            json={"status": "evidence_gathering", "statusRationale": "Collecting field samples"},
            headers=invHeaders,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/cases/{caseOneId}/status",
            json={
                "status": "field_verification_required",
                "statusRationale": "Need instrument reading",
            },
            headers=invHeaders,
        ).status_code
        == 200
    )

    singleKeyFail = client.post(
        f"/api/v1/cases/{caseOneId}/status",
        json={
            "status": "field_verified",
            "statusRationale": "Confirmed in field",
            "fieldRecordReference": "FLD-2026-009",
        },
        headers=specHeaders,
    )
    assert singleKeyFail.status_code == 409
    assert singleKeyFail.json()["code"] == "TWO_KEY_APPROVAL_REQUIRED"

    esApprove = client.post(
        f"/api/v1/cases/{caseOneId}/field-verification-approvals",
        json={
            "approvalRole": "specialist",
            "fieldRecordReference": "FLD-2026-009",
        },
        headers=specHeaders,
    )
    assert esApprove.status_code == 200
    assert esApprove.json()["readyForFieldVerified"] is False

    oaApprove = client.post(
        f"/api/v1/cases/{caseOneId}/field-verification-approvals",
        json={"approvalRole": "authority"},
        headers=oaHeaders,
    )
    assert oaApprove.status_code == 200
    assert oaApprove.json()["readyForFieldVerified"] is True

    verifiedResp = client.post(
        f"/api/v1/cases/{caseOneId}/status",
        json={"status": "field_verified", "statusRationale": "Two-key verification complete"},
        headers=oaHeaders,
    )
    assert verifiedResp.status_code == 200
    assert verifiedResp.json()["status"] == "field_verified"

    blockedRecovery = client.post(
        f"/api/v1/cases/{caseOneId}/status",
        json={"status": "recovery_verified", "statusRationale": "Not allowed in Phase 1"},
        headers=oaHeaders,
    )
    assert blockedRecovery.status_code == 409
    assert blockedRecovery.json()["code"] == "INVALID_STATUS_TRANSITION"

    timelineResp = client.get(f"/api/v1/cases/{caseOneId}/timeline", headers=invHeaders)
    assert timelineResp.status_code == 200
    dateTypes = {item["dateType"] for item in timelineResp.json()["items"]}
    assert {
        "event_start_at",
        "observed_at",
        "submitted_at",
        "received_at",
        "case.status_changed",
    }.issubset(dateTypes)

    assert client.get("/api/v1/public/cases").json()["items"] == []
    draftSummary = client.patch(
        f"/api/v1/cases/{caseOneId}",
        json={"publicSummary": "Field team verified elevated turbidity near culvert."},
        headers=specHeaders,
    )
    assert draftSummary.status_code == 200
    assert client.get("/api/v1/public/cases").json()["items"] == []
    approveSummary = client.patch(
        f"/api/v1/cases/{caseOneId}",
        json={"isPublicSummaryApproved": True},
        headers=oaHeaders,
    )
    assert approveSummary.status_code == 200

    publicList = client.get("/api/v1/public/cases")
    assert publicList.status_code == 200
    assert len(publicList.json()["items"]) == 1
    publicItem = publicList.json()["items"][0]
    assert publicItem["publicSummary"] == "Field team verified elevated turbidity near culvert."
    assert "summary" not in publicItem
    assert "areaGeometry" not in publicItem

    closedResp = client.post(
        f"/api/v1/cases/{caseOneId}/status",
        json={"status": "closed", "statusRationale": "Investigation handed over"},
        headers=invHeaders,
    )
    assert closedResp.status_code == 200
    reopenFail = client.post(
        f"/api/v1/cases/{caseOneId}/status",
        json={"status": "recovery_verified", "statusRationale": "Illegal reopen"},
        headers=oaHeaders,
    )
    assert reopenFail.status_code == 409

    auditActions = {
        row.action for row in dbSession.execute(select(AuditEvent)).scalars().all()
    }
    assert {"case.created", "case_observation.linked", "case.status_changed"}.issubset(auditActions)
