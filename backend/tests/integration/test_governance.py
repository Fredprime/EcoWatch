"""FR-057 governance: tombstone erasure (keep originals) and organisation data export."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.spatial import format_point_wkt
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.identity.models import Organisation, User
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.observations.models import Observation, ObservationSource
from tests.conftest import auth_headers, create_temp_org, create_temp_user


def make_observation(
    dbSession: Session,
    org: Organisation,
    *,
    submittedBy: User | None = None,
) -> Observation:
    """Temporary observation with only the fields governance reads set explicitly."""
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
        submittedByUserId=submittedBy.id if submittedBy else None,
    )
    dbSession.add(obs)
    dbSession.flush()
    dbSession.add(
        ObservationSource(
            observationId=obs.id,
            reporterName="Ama Boateng",
            contactChannel="phone",
            contactValue="+233200000000",
            consentGiven=True,
            privacyNoticeVersion="v1",
            safetyAck=True,
            clientMetadata={"ip": "203.0.113.9"},
        )
    )
    dbSession.commit()
    return obs


def hide_observation(client: TestClient, observationId: uuid.UUID, headers: dict[str, str]):
    return client.post(
        f"/api/v1/observations/{observationId}/hide",
        json={"reason": "erasure request under approved policy"},
        headers=headers,
    )


def test_hide_tombstones_without_deleting_originals(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    sa = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    member = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    obs = make_observation(dbSession, org, submittedBy=member)

    resp = hide_observation(client, obs.id, auth_headers(authProvider, sa))
    assert resp.status_code == 200
    assert resp.json()["isHidden"] is True

    # Originals are preserved: the row, source row and identity-free flags remain.
    assert dbSession.get(Observation, obs.id) is not None
    source = (
        dbSession.query(ObservationSource)
        .filter(ObservationSource.observationId == obs.id)
        .one()
    )
    assert source.reporterName is None
    assert source.contactChannel is None
    assert source.contactValue is None
    assert source.clientMetadata is None

    audit = (
        dbSession.query(AuditEvent)
        .filter(AuditEvent.action == "observation.hidden", AuditEvent.targetId == obs.id)
        .one()
    )
    assert audit.organisationId == org.id
    assert audit.reason == "erasure request under approved policy"

    # Hidden records disappear from staff list/detail and from receipt lookup paths.
    memberHeaders = auth_headers(authProvider, member)
    assert client.get(f"/api/v1/observations/{obs.id}", headers=memberHeaders).status_code == 404
    listed = client.get("/api/v1/observations", headers=memberHeaders).json()["items"]
    assert all(item["id"] != str(obs.id) for item in listed)


def test_hide_is_system_admin_only_and_idempotent(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    sa = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    oa = create_temp_user(dbSession, memberships=[(org.id, Role.ORGANISATION_ADMIN)])
    outsider = create_temp_user(dbSession)
    obs = make_observation(dbSession, org)

    assert hide_observation(client, obs.id, auth_headers(authProvider, oa)).status_code == 403
    assert hide_observation(client, obs.id, auth_headers(authProvider, outsider)).status_code == 404

    saHeaders = auth_headers(authProvider, sa)
    assert hide_observation(client, obs.id, saHeaders).status_code == 200
    assert hide_observation(client, obs.id, saHeaders).status_code == 200
    count = (
        dbSession.query(AuditEvent)
        .filter(AuditEvent.action == "observation.hidden", AuditEvent.targetId == obs.id)
        .count()
    )
    assert count == 1


def test_export_is_owner_or_admin_scoped_and_includes_hidden_records(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    otherOrg = create_temp_org(dbSession)
    oa = create_temp_user(dbSession, memberships=[(org.id, Role.ORGANISATION_ADMIN)])
    sa = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    visible = make_observation(dbSession, org)
    hidden = make_observation(dbSession, org)
    hidden.isHidden = True
    dbSession.commit()
    make_observation(dbSession, otherOrg)

    url = f"/api/v1/observations/export?organisationId={org.id}"

    assert client.get(url, headers=auth_headers(authProvider, investigator)).status_code == 403
    crossOrg = client.get(
        f"/api/v1/observations/export?organisationId={otherOrg.id}",
        headers=auth_headers(authProvider, oa),
    )
    assert crossOrg.status_code == 404

    resp = client.get(url, headers=auth_headers(authProvider, oa))
    assert resp.status_code == 200
    body = resp.json()
    assert body["organisationId"] == str(org.id)
    ids = {record["observation"]["id"] for record in body["observations"]}
    assert ids == {str(visible.id), str(hidden.id)}
    assert all("source" in record and "versions" in record for record in body["observations"])

    saResp = client.get(url, headers=auth_headers(authProvider, sa))
    assert saResp.status_code == 200
    assert len(saResp.json()["observations"]) == 2

    assert (
        dbSession.query(AuditEvent)
        .filter(AuditEvent.action == "observation.exported", AuditEvent.targetId == org.id)
        .count()
        == 2
    )
