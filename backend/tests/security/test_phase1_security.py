"""Security, isolation, separation-of-duties, and input-safety tests for Phase 1."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.identity.permissions import Principal, Role, SystemRole
from ecowatch.modules.observations.models import AccessClass
from tests.conftest import (
    auth_headers,
    create_temp_org,
    create_temp_user,
    make_jpeg_with_exif_bytes,
)


def test_cross_organisation_isolation_returns_404(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: LocalFilesystemStorage,
    testSettings: Settings,
) -> None:
    orgA = create_temp_org(dbSession, name="Org A")
    orgB = create_temp_org(dbSession, name="Org B")

    adminA = create_temp_user(dbSession, memberships=[(orgA.id, Role.ORGANISATION_ADMIN)])
    invB = create_temp_user(dbSession, memberships=[(orgB.id, Role.INVESTIGATOR)])
    headersA = auth_headers(authProvider, adminA)
    headersB = auth_headers(authProvider, invB)

    obsB = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(orgB.id),
            "observationType": "land_clearing",
            "description": "Org B confidential observation",
            "source": {"reporterName": "Secret Reporter", "consentGiven": True},
        },
        headers=headersB,
    )
    assert obsB.status_code == 201
    obsBId = uuid.UUID(obsB.json()["observationId"])

    caseB = client.post(
        "/api/v1/cases",
        json={
            "organisationId": str(orgB.id),
            "title": "Org B Case",
            "summary": "Confidential",
        },
        headers=headersB,
    )
    assert caseB.status_code == 201
    caseBId = caseB.json()["id"]

    invBPrincipal = Principal(
        userId=invB.id, memberships=((orgB.id, Role.INVESTIGATOR),), isAuthenticated=True
    )
    assetB = EvidenceService(dbSession, storageProvider).upload_evidence(
        invBPrincipal,
        obsBId,
        rawBytes=make_jpeg_with_exif_bytes(),
        filename="b.jpg",
        declaredMimeType="image/jpeg",
        accessClass=AccessClass.RESTRICTED,
        trackingCode=None,
        settings=testSettings,
        requestId=None,
    )

    assert client.get(f"/api/v1/observations/{obsBId}", headers=headersA).status_code == 404
    assert client.get(f"/api/v1/observations/{obsBId}/source", headers=headersA).status_code == 404
    assert client.get(f"/api/v1/cases/{caseBId}", headers=headersA).status_code == 404
    assert client.get(f"/api/v1/evidence/{assetB.id}/original", headers=headersA).status_code == 404


def test_anonymous_and_source_isolation_boundaries(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    orgAdmin = create_temp_user(dbSession, memberships=[(org.id, Role.ORGANISATION_ADMIN)])
    revHeaders = auth_headers(authProvider, reviewer)
    oaHeaders = auth_headers(authProvider, orgAdmin)

    obsResp = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "spill",
            "description": "Sheen on stream",
            "lat": 6.1234,
            "lon": -1.5678,
            "locationPrecision": "exact",
            "source": {
                "reporterName": "Protected Witness",
                "contactChannel": "email",
                "contactValue": "witness@example.test",
                "consentGiven": True,
            },
        },
    )
    assert obsResp.status_code == 201
    obsId = obsResp.json()["observationId"]

    assert client.get("/api/v1/observations").status_code == 401
    assert client.get("/api/v1/cases").status_code == 401
    assert client.get("/api/v1/audit/events").status_code == 401
    assert client.get("/api/v1/jobs").status_code == 401

    revObs = client.get(f"/api/v1/observations/{obsId}", headers=revHeaders)
    assert revObs.status_code == 200
    assert "source" not in revObs.json()
    assert "reporterName" not in revObs.json()
    assert "location" not in revObs.json()
    assert revObs.json()["publicLocation"] == {"lat": 6.12, "lon": -1.57}

    assert client.get(f"/api/v1/observations/{obsId}/source", headers=revHeaders).status_code == 403

    oaSource = client.get(f"/api/v1/observations/{obsId}/source", headers=oaHeaders)
    assert oaSource.status_code == 200
    assert oaSource.json()["reporterName"] == "Protected Witness"

    sourceAudits = dbSession.execute(
        select(AuditEvent).where(AuditEvent.action == "observation_source.viewed")
    ).scalars().all()
    assert len(sourceAudits) == 1


def test_self_review_and_admin_scientific_boundaries(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    dualUser = create_temp_user(
        dbSession,
        memberships=[
            (org.id, Role.REVIEWER),
            (org.id, Role.INVESTIGATOR),
            (org.id, Role.ENVIRONMENTAL_SPECIALIST),
        ],
    )
    otherInv = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    sysAdmin = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)

    dualHeaders = auth_headers(authProvider, dualUser)
    otherHeaders = auth_headers(authProvider, otherInv)
    saHeaders = auth_headers(authProvider, sysAdmin)

    obsResp = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "erosion",
            "description": "Gully erosion near slope",
        },
        headers=dualHeaders,
    )
    assert obsResp.status_code == 201
    obsId = obsResp.json()["observationId"]

    caseResp = client.post(
        "/api/v1/cases",
        json={"organisationId": str(org.id), "title": "Slope Case", "summary": "Test"},
        headers=otherHeaders,
    )
    assert caseResp.status_code == 201
    caseId = caseResp.json()["id"]

    selfLink = client.post(
        f"/api/v1/cases/{caseId}/observations",
        json={"observationId": obsId, "linkRationale": "Self review attempt"},
        headers=dualHeaders,
    )
    assert selfLink.status_code == 403
    assert selfLink.json()["code"] == "SELF_REVIEW_FORBIDDEN"

    saApproval = client.post(
        f"/api/v1/cases/{caseId}/field-verification-approvals",
        json={"approvalRole": "specialist"},
        headers=saHeaders,
    )
    assert saApproval.status_code == 403


def test_evidence_upload_rejects_spoofed_and_oversized_payloads(
    dbSession: Session,
    storageProvider: LocalFilesystemStorage,
    testSettings: Settings,
) -> None:
    org = create_temp_org(dbSession)
    user = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    principal = Principal(
        userId=user.id, memberships=((org.id, Role.INVESTIGATOR),), isAuthenticated=True
    )

    from ecowatch.modules.collection.schemas import CreateObservationRequest
    from ecowatch.modules.collection.service import CollectionService

    receipt, _replayed = CollectionService(dbSession).submit_observation(
        principal,
        CreateObservationRequest(
            idempotencyKey=uuid.uuid4(),
            organisationId=org.id,
            observationType="waste",
            description="Dumped drums",
        ),
        settings=testSettings,
        clientIp="127.0.0.1",
        requestId=None,
    )

    service = EvidenceService(dbSession, storageProvider)
    elfPayload = b"\x7fELF" + b"\x00" * 64
    try:
        service.upload_evidence(
            principal,
            receipt.observationId,
            rawBytes=elfPayload,
            filename="../../evil.jpg",
            declaredMimeType="image/jpeg",
            accessClass=AccessClass.RESTRICTED,
            trackingCode=None,
            settings=testSettings,
            requestId=None,
        )
        raise AssertionError("Expected DomainError for spoofed MIME type")
    except Exception as exc:
        assert getattr(exc, "code", None) == "UNSUPPORTED_MEDIA_TYPE"

    oversized = b"\xff\xd8\xff\xe0" + b"a" * (testSettings.maxUploadBytes + 1)
    try:
        service.upload_evidence(
            principal,
            receipt.observationId,
            rawBytes=oversized,
            filename="huge.jpg",
            declaredMimeType="image/jpeg",
            accessClass=AccessClass.RESTRICTED,
            trackingCode=None,
            settings=testSettings,
            requestId=None,
        )
        raise AssertionError("Expected DomainError for oversized upload")
    except Exception as exc:
        assert getattr(exc, "code", None) == "PAYLOAD_TOO_LARGE"
