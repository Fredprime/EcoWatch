"""Case field_verified two-key governance: human approval records only."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.cases.models import Case
from ecowatch.modules.identity.permissions import Role, SystemRole
from tests.conftest import auth_headers, create_temp_org, create_temp_user


def _principal(
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    orgId: uuid.UUID,
    role: Role,
):
    """Create a temporary role holder in one organisation."""
    user = create_temp_user(dbSession, memberships=[(orgId, role)])
    return user, auth_headers(authProvider, user)


def _ready_case(
    client: TestClient,
    *,
    orgId: uuid.UUID,
    creatorHeaders: dict[str, str],
    transitionHeaders: dict[str, str],
    leadUserId: uuid.UUID | None = None,
) -> str:
    """Create a temporary case and advance it to field_verification_required."""
    payload: dict[str, object] = {
        "organisationId": str(orgId),
        "title": "Two-key field review",
        "summary": "Temporary case for two-key verification testing",
    }
    if leadUserId is not None:
        payload["leadInvestigatorId"] = str(leadUserId)
    created = client.post("/api/v1/cases", json=payload, headers=creatorHeaders)
    assert created.status_code == 201, created.text
    caseId = created.json()["id"]
    for statusValue in ("evidence_gathering", "field_verification_required"):
        moved = client.post(
            f"/api/v1/cases/{caseId}/status",
            json={"status": statusValue, "statusRationale": "Preparing field verification"},
            headers=transitionHeaders,
        )
        assert moved.status_code == 200, moved.text
    return caseId


def _verify_payload(
    specialistId: uuid.UUID,
    authorityId: uuid.UUID,
    **overrides: object,
) -> dict[str, object]:
    """Build a field_verified transition with explicit human approver keys."""
    return {
        "status": "field_verified",
        "statusRationale": "Human field conclusion recorded",
        "fieldRecordReference": "FLD-TWO-KEY-001",
        "specialistApproverUserId": str(specialistId),
        "authorityApproverUserId": str(authorityId),
        **overrides,
    }


def test_case_field_verified_records_both_keys_and_audit(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    owner, ownerHeaders = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    specialist, specialistHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    authority, _ = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    caseId = _ready_case(
        client, orgId=orgId, creatorHeaders=ownerHeaders, transitionHeaders=ownerHeaders
    )

    approved = client.post(
        f"/api/v1/cases/{caseId}/status",
        json=_verify_payload(specialist.id, authority.id),
        headers=specialistHeaders,
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == "field_verified"
    assert body["specialistApproverUserId"] == str(specialist.id)
    assert body["authorityApproverUserId"] == str(authority.id)
    assert body["twoKeyApprovedAt"] is not None

    stored = client.get(f"/api/v1/cases/{caseId}", headers=ownerHeaders).json()
    assert stored["specialistApproverUserId"] == str(specialist.id)
    assert stored["authorityApproverUserId"] == str(authority.id)
    assert stored["twoKeyApprovedAt"] is not None
    assert stored["specialistApprovalUserId"] == str(specialist.id)
    assert stored["authorityApprovalUserId"] == str(authority.id)

    event = dbSession.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "case.status_changed", AuditEvent.targetId == uuid.UUID(caseId))
        .order_by(AuditEvent.occurredAt.desc())
    )
    assert event is not None
    assert event.details["specialistApproverUserId"] == str(specialist.id)
    assert event.details["authorityApproverUserId"] == str(authority.id)


def test_case_field_verified_denies_incomplete_and_mismatched_keys(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    owner, ownerHeaders = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    specialist, specialistHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    authority, authorityHeaders = _principal(
        dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN
    )
    caseId = _ready_case(
        client, orgId=orgId, creatorHeaders=ownerHeaders, transitionHeaders=ownerHeaders
    )
    path = f"/api/v1/cases/{caseId}/status"

    missing = client.post(
        path,
        json=_verify_payload(specialist.id, authority.id, authorityApproverUserId=None),
        headers=specialistHeaders,
    )
    assert missing.status_code == 400, missing.text
    assert missing.json()["code"] == "TWO_KEY_APPROVAL_REQUIRED"

    sameUser = client.post(
        path,
        json=_verify_payload(specialist.id, specialist.id),
        headers=specialistHeaders,
    )
    assert sameUser.status_code == 400, sameUser.text
    assert sameUser.json()["code"] == "TWO_KEY_APPROVAL_REQUIRED"

    swappedRoles = client.post(
        path,
        json=_verify_payload(authority.id, specialist.id),
        headers=specialistHeaders,
    )
    assert swappedRoles.status_code == 400, swappedRoles.text
    assert swappedRoles.json()["code"] == "TWO_KEY_APPROVAL_REQUIRED"

    absentActor = client.post(
        path,
        json=_verify_payload(specialist.id, authority.id),
        headers=ownerHeaders,
    )
    assert absentActor.status_code == 403, absentActor.text
    assert absentActor.json()["code"] == "FORBIDDEN"

    otherAuthority, otherHeaders = _principal(
        dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN
    )
    otherKeys = client.post(
        path,
        json=_verify_payload(specialist.id, otherAuthority.id),
        headers=authorityHeaders,
    )
    assert otherKeys.status_code == 403, otherKeys.text
    assert otherKeys.json()["code"] == "FORBIDDEN"

    systemAdmin = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    systemApproval = client.post(
        path,
        json=_verify_payload(specialist.id, authority.id),
        headers=auth_headers(authProvider, systemAdmin),
    )
    assert systemApproval.status_code == 403, systemApproval.text
    assert systemApproval.json()["code"] == "FORBIDDEN"

    assert client.get(f"/api/v1/cases/{caseId}", headers=ownerHeaders).json()["status"] == (
        "field_verification_required"
    )


def test_case_field_verified_denies_owner_lead_and_observation_submitter(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    setupAdmin, setupHeaders = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    authority, _ = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    owner = create_temp_user(
        dbSession,
        memberships=[
            (orgId, Role.ORGANISATION_ADMIN),
            (orgId, Role.ENVIRONMENTAL_SPECIALIST),
        ],
    )
    ownerHeaders = auth_headers(authProvider, owner)
    lead, leadHeaders = _principal(dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST)
    submitter, submitterHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    linker, linkerHeaders = _principal(dbSession, authProvider, orgId, Role.INVESTIGATOR)

    ownedCase = _ready_case(
        client, orgId=orgId, creatorHeaders=ownerHeaders, transitionHeaders=setupHeaders
    )
    ownerApproval = client.post(
        f"/api/v1/cases/{ownedCase}/status",
        json=_verify_payload(owner.id, authority.id),
        headers=ownerHeaders,
    )
    assert ownerApproval.status_code == 400, ownerApproval.text
    assert ownerApproval.json()["field"] == "approverUserIds"

    leadCase = _ready_case(
        client,
        orgId=orgId,
        creatorHeaders=setupHeaders,
        transitionHeaders=setupHeaders,
        leadUserId=lead.id,
    )
    leadApproval = client.post(
        f"/api/v1/cases/{leadCase}/status",
        json=_verify_payload(lead.id, authority.id),
        headers=leadHeaders,
    )
    assert leadApproval.status_code == 400, leadApproval.text
    assert leadApproval.json()["field"] == "approverUserIds"

    submitterCase = _ready_case(
        client, orgId=orgId, creatorHeaders=setupHeaders, transitionHeaders=setupHeaders
    )
    observed = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(orgId),
            "observationType": "river_foam",
            "description": "Temporary observation for self-review denial",
        },
        headers=submitterHeaders,
    )
    assert observed.status_code == 201, observed.text
    linked = client.post(
        f"/api/v1/cases/{submitterCase}/observations",
        json={
            "observationId": observed.json()["observationId"],
            "linkRationale": "Linked by an uninvolved administrator",
        },
        headers=linkerHeaders,
    )
    assert linked.status_code == 201, linked.text
    submitterApproval = client.post(
        f"/api/v1/cases/{submitterCase}/status",
        json=_verify_payload(submitter.id, authority.id),
        headers=submitterHeaders,
    )
    assert submitterApproval.status_code == 403, submitterApproval.text
    assert submitterApproval.json()["code"] == "SELF_REVIEW_FORBIDDEN"

    case = dbSession.get(Case, uuid.UUID(leadCase))
    assert case is not None
    assert case.twoKeyApprovedAt is None
