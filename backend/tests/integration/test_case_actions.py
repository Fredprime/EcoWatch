"""ADR-031 case-side correlation actions with ADR-035 single-actor authority."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.spatial import format_point_wkt
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.cases.models import Case, CaseObservation, CaseStatus
from ecowatch.modules.correlation.models import CorrelationCluster, CorrelationClusterMember
from ecowatch.modules.identity.models import Organisation, User
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.observations.models import Observation
from tests.conftest import auth_headers, create_temp_org, create_temp_user


def make_observation(
    dbSession: Session,
    org: Organisation,
    *,
    submittedBy: User | None = None,
) -> Observation:
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
    dbSession.commit()
    return obs


def make_case(
    dbSession: Session,
    org: Organisation,
    creator: User,
    code: str,
) -> Case:
    case = Case(
        organisationId=org.id,
        caseCode=code,
        title=f"Case {code}",
        summary="Investigation summary",
        status=CaseStatus.NEW_UNREVIEWED.value,
        statusRationale="Initial case creation",
        accessClass="internal",
        createdByUserId=creator.id,
        investigationQuestions=[],
        competingHypotheses=[],
        evidenceGaps=[],
    )
    dbSession.add(case)
    dbSession.commit()
    return case


def link(dbSession: Session, case: Case, obs: Observation) -> CaseObservation:
    row = CaseObservation(
        caseId=case.id,
        observationId=obs.id,
        linkRationale="Reviewed link",
        proposedByType="human",
        proposedByUserId=None,
        reviewStatus="accepted",
        reviewedByUserId=None,
        reviewedAt=None,
        isContested=False,
        contestedNote=None,
    )
    dbSession.add(row)
    dbSession.commit()
    return row


def make_cluster(
    dbSession: Session, org: Organisation, observations: list[Observation]
) -> CorrelationCluster:
    cluster = CorrelationCluster(organisationId=org.id)
    dbSession.add(cluster)
    dbSession.flush()
    for obs in observations:
        dbSession.add(CorrelationClusterMember(clusterId=cluster.id, observationId=obs.id))
    dbSession.commit()
    return cluster


def case_links(dbSession: Session, caseId: uuid.UUID) -> set[uuid.UUID]:
    return {
        row.observationId
        for row in dbSession.query(CaseObservation)
        .filter(CaseObservation.caseId == caseId)
        .all()
    }


def test_promote_cluster_authority_and_result(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    otherOrg = create_temp_org(dbSession)
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    specialist = create_temp_user(
        dbSession, memberships=[(org.id, Role.ENVIRONMENTAL_SPECIALIST)]
    )
    outsider = create_temp_user(dbSession)
    first = make_observation(dbSession, org)
    second = make_observation(dbSession, org)
    cluster = make_cluster(dbSession, org, [first, second])
    payload = {
        "clusterId": str(cluster.id),
        "title": "Promoted cluster",
        "summary": "Two reviewed reports",
        "statusRationale": "Cluster reviewed by investigator",
    }

    assert (
        client.post(
            "/api/v1/cases/promote-from-cluster",
            json=payload,
            headers=auth_headers(authProvider, specialist),
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/cases/promote-from-cluster",
            json=payload,
            headers=auth_headers(authProvider, outsider),
        ).status_code
        == 404
    )

    resp = client.post(
        "/api/v1/cases/promote-from-cluster",
        json=payload,
        headers=auth_headers(authProvider, investigator),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["action"] == "promote_to_case"
    assert body["case"]["organisationId"] == str(org.id)
    newCaseId = uuid.UUID(body["case"]["id"])
    assert case_links(dbSession, newCaseId) == {first.id, second.id}
    assert set(body["affectedObservationIds"]) == {str(first.id), str(second.id)}

    audit = (
        dbSession.query(AuditEvent)
        .filter(
            AuditEvent.action == "case.promoted_from_cluster",
            AuditEvent.targetId == newCaseId,
        )
        .one()
    )
    assert audit.organisationId == org.id

    # A cross-organisation actor cannot promote this cluster.
    crossOrgUser = create_temp_user(dbSession, memberships=[(otherOrg.id, Role.INVESTIGATOR)])
    assert (
        client.post(
            "/api/v1/cases/promote-from-cluster",
            json=payload,
            headers=auth_headers(authProvider, crossOrgUser),
        ).status_code
        == 404
    )


def test_promote_blocks_self_submitted_observation(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    own = make_observation(dbSession, org, submittedBy=investigator)
    cluster = make_cluster(dbSession, org, [own])

    resp = client.post(
        "/api/v1/cases/promote-from-cluster",
        json={
            "clusterId": str(cluster.id),
            "title": "Self review",
            "summary": "Should be blocked",
        },
        headers=auth_headers(authProvider, investigator),
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "SELF_REVIEW_FORBIDDEN"


def test_merge_moves_all_links_and_retains_source(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    source = make_case(dbSession, org, investigator, "CASE-MERGE-SRC")
    target = make_case(dbSession, org, investigator, "CASE-MERGE-DST")
    first = make_observation(dbSession, org)
    second = make_observation(dbSession, org)
    link(dbSession, source, first)
    link(dbSession, source, second)

    resp = client.post(
        f"/api/v1/cases/{source.id}/merge",
        json={"targetCaseId": str(target.id), "statusRationale": "Duplicates"},
        headers=auth_headers(authProvider, investigator),
    )
    assert resp.status_code == 200
    assert resp.json()["action"] == "merge"
    assert case_links(dbSession, source.id) == set()
    assert case_links(dbSession, target.id) == {first.id, second.id}

    dbSession.refresh(source)
    assert source.status == CaseStatus.MERGED.value
    assert source.mergedIntoCaseId == target.id

    actions = {
        event.action
        for event in dbSession.query(AuditEvent)
        .filter(AuditEvent.organisationId == org.id)
        .all()
    }
    assert {"case.merged", "case.merge_received"} <= actions

    # Cross-organisation merge target is hidden as not found.
    otherOrg = create_temp_org(dbSession)
    otherCase = make_case(dbSession, otherOrg, investigator, "CASE-MERGE-OTHER")
    resp = client.post(
        f"/api/v1/cases/{target.id}/merge",
        json={"targetCaseId": str(otherCase.id), "statusRationale": "Cross org"},
        headers=auth_headers(authProvider, investigator),
    )
    assert resp.status_code == 404


def test_split_moves_subset_into_new_case(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    oa = create_temp_user(dbSession, memberships=[(org.id, Role.ORGANISATION_ADMIN)])
    source = make_case(dbSession, org, oa, "CASE-SPLIT-SRC")
    first = make_observation(dbSession, org)
    second = make_observation(dbSession, org)
    third = make_observation(dbSession, org)
    for obs in (first, second, third):
        link(dbSession, source, obs)

    resp = client.post(
        f"/api/v1/cases/{source.id}/split",
        json={
            "observationIds": [str(first.id), str(second.id)],
            "title": "Split case",
            "summary": "Separate thread",
        },
        headers=auth_headers(authProvider, oa),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["action"] == "split"
    newCaseId = uuid.UUID(body["case"]["id"])
    assert case_links(dbSession, source.id) == {third.id}
    assert case_links(dbSession, newCaseId) == {first.id, second.id}

    actions = {
        event.action for event in dbSession.query(AuditEvent).all()
    }
    assert {"case.split_source", "case.split_created"} <= actions


def test_cross_case_moves_selected_links_between_cases(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    sa = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    source = make_case(dbSession, org, sa, "CASE-CROSS-SRC")
    target = make_case(dbSession, org, sa, "CASE-CROSS-DST")
    first = make_observation(dbSession, org)
    second = make_observation(dbSession, org)
    link(dbSession, source, first)
    link(dbSession, source, second)

    resp = client.post(
        "/api/v1/cases/cross-case",
        json={
            "sourceCaseId": str(source.id),
            "targetCaseId": str(target.id),
            "observationIds": [str(first.id)],
            "linkRationale": "Belongs with the target thread",
        },
        headers=auth_headers(authProvider, sa),
    )
    assert resp.status_code == 200
    assert resp.json()["action"] == "cross_case"
    assert case_links(dbSession, source.id) == {second.id}
    assert case_links(dbSession, target.id) == {first.id}
    assert (
        dbSession.query(AuditEvent).filter(AuditEvent.action == "case.cross_case_moved").count()
        == 1
    )
