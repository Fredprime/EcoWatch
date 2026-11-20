"""Integration tests for the ADR-037 org-scoped Phase 3 read APIs.

Every record is created through the existing write endpoints inside an isolated
temporary database; fixture teardown removes it. No product seed data is used.
"""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.catalogue import models as catalogue_models  # noqa: F401
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.intelligence import models as intelligence_models  # noqa: F401
from ecowatch.modules.interventions import models as intervention_models  # noqa: F401
from ecowatch.modules.jobs.worker import run_once
from ecowatch.modules.observations.models import Unit
from ecowatch.modules.prioritisation import models as prioritisation_models  # noqa: F401
from ecowatch.modules.verification import models as verification_models  # noqa: F401
from tests.conftest import auth_headers, create_temp_org, create_temp_user

NOW = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)

TOP_LEVEL_LISTS = (
    ("entities", "/api/v1/intelligence/entities"),
    ("relationships", "/api/v1/intelligence/relationships"),
    ("analyses", "/api/v1/intelligence/analyses"),
    ("datasets", "/api/v1/catalogue/datasets"),
    ("prioritisation", "/api/v1/prioritisation/assessments"),
    ("interventions", "/api/v1/interventions/interventions"),
    ("indicators", "/api/v1/verification/indicators"),
    ("measurements", "/api/v1/verification/measurements"),
    ("verification", "/api/v1/verification/assessments"),
    ("publications", "/api/v1/verification/publications"),
)


def _actor(
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    role: Role = Role.ENVIRONMENTAL_SPECIALIST,
    *,
    systemRole: SystemRole | None = None,
) -> tuple[uuid.UUID, dict[str, str], uuid.UUID]:
    """Create a temporary organisation and an authenticated principal."""
    org = create_temp_org(dbSession)
    memberships = [] if systemRole is not None else [(org.id, role)]
    user = create_temp_user(dbSession, memberships=memberships, systemRole=systemRole)
    return org.id, auth_headers(authProvider, user), user.id


def _temp_unit(dbSession: Session) -> uuid.UUID:
    """Create a temporary controlled unit used by measurement records."""
    unit = Unit(
        symbol=f"NTU-{uuid.uuid4().hex[:8]}", name="Turbidity", dimension="turbidity"
    )
    dbSession.add(unit)
    dbSession.commit()
    return unit.id


def _seed(
    client: TestClient,
    dbSession: Session,
    storageProvider: StorageProvider,
    headers: dict[str, str],
    orgId: uuid.UUID,
    unitId: uuid.UUID,
    specialistApproverUserId: uuid.UUID,
) -> dict[str, str]:
    """Create one temporary record of every Phase 3 type through the write APIs."""
    ids: dict[str, str] = {}
    org = str(orgId)

    response = client.post(
        "/api/v1/intelligence/entities",
        headers=headers,
        json={
            "organisationId": org,
            "entityType": "catchment",
            "name": "Upper catchment",
            "geometry": "POLYGON((0 0, 1 0, 1 1, 0 0))",
        },
    )
    assert response.status_code == 201, response.text
    ids["entity"] = response.json()["id"]

    response = client.post(
        "/api/v1/intelligence/relationships",
        headers=headers,
        json={
            "organisationId": org,
            "relationshipType": "upstream_downstream",
            "evidenceSummary": "Observations follow the inferred flow direction.",
            "uncertainty": "medium",
            "uncertaintyNote": "Flow direction is inferred from a coarse model.",
            "alternativeExplanations": "A separate source may contribute.",
            "methodName": "CatchmentPathway",
            "methodVersion": "1.0",
            "fromEntityId": ids["entity"],
            "toObservationId": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 201, response.text
    ids["relationship"] = response.json()["id"]

    response = client.post(
        "/api/v1/catalogue/datasets",
        headers=headers,
        json={
            "organisationId": org,
            "name": f"River turbidity baseline {uuid.uuid4().hex[:6]}",
            "owner": "EcoWatch",
            "licence": "CC-BY-4.0",
            "attribution": "EcoWatch field team",
            "permittedUse": "Environmental monitoring",
            "crs": "EPSG:4326",
            "coverageStartAt": NOW.isoformat(),
            "coverageGeometry": "POINT(0.1 5.6)",
        },
    )
    assert response.status_code == 201, response.text
    ids["dataset"] = response.json()["id"]

    response = client.post(
        f"/api/v1/catalogue/datasets/{ids['dataset']}/versions",
        headers=headers,
        json={
            "organisationId": org,
            "versionLabel": "v1",
            "sourceAcquisitionAt": NOW.isoformat(),
            "resolution": "10m",
            "crs": "EPSG:4326",
            "method": "Field sampling",
            "licence": "CC-BY-4.0",
            "attribution": "EcoWatch field team",
            "permittedUse": "Environmental monitoring",
        },
    )
    assert response.status_code == 201, response.text
    ids["version"] = response.json()["id"]

    # Give the stored version real bytes so the worker's real execution succeeds.
    versionRow = dbSession.get(catalogue_models.DatasetVersion, uuid.UUID(ids["version"]))
    assert versionRow is not None
    storageKey = f"datasets/{uuid.uuid4().hex}.csv"
    versionRow.storageKey = storageKey
    storageProvider.put_bytes(storageKey, b"site,reading\nA,1.5\nB,2.5\n")
    dbSession.commit()

    response = client.post(
        "/api/v1/intelligence/analyses",
        headers=headers,
        json={
            "organisationId": org,
            "question": "Did bare soil increase?",
            "analysisType": "land_cover_change",
            "methodName": "NDVIThreshold",
            "methodVersion": "1.0",
            "inputDatasetVersionIds": [ids["version"]],
            "crs": "EPSG:4326",
            "parameters": {"threshold": 0.2},
            "limitations": "Cloud cover in one month.",
        },
    )
    assert response.status_code == 202, response.text
    ids["run"] = response.json()["id"]
    # Advance the real queued job; the worker writes one derived output for the run.
    assert run_once(dbSession, storageProvider) == 1

    response = client.post(
        "/api/v1/prioritisation/assessments",
        headers=headers,
        json={
            "organisationId": org,
            "caseId": str(uuid.uuid4()),
            "methodName": "TransparentFactors",
            "methodVersion": "1.0",
            "factors": {"magnitude": "large", "extent": None},
            "compositeRank": 2.0,
            "rankingMethodRef": "docs/prioritisation-method.md",
            "rankIsNotSeverity": True,
        },
    )
    assert response.status_code == 201, response.text
    ids["prioritisation"] = response.json()["id"]

    response = client.post(
        "/api/v1/interventions/interventions",
        headers=headers,
        json={
            "organisationId": org,
            "caseId": str(uuid.uuid4()),
            "objective": "Reduce sediment entering the catchment.",
            "responsibleOrganisationId": org,
            "authorisedLeadUserId": str(uuid.uuid4()),
            "location": "POINT(0.2 5.7)",
        },
    )
    assert response.status_code == 201, response.text
    ids["intervention"] = response.json()["id"]

    response = client.post(
        f"/api/v1/interventions/interventions/{ids['intervention']}/milestones",
        headers=headers,
        json={
            "organisationId": org,
            "name": "Install sediment traps",
            "plannedAt": NOW.isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    ids["milestone"] = response.json()["id"]

    response = client.post(
        "/api/v1/verification/indicators",
        headers=headers,
        json={
            "organisationId": org,
            "code": f"TURB-{uuid.uuid4().hex[:6]}",
            "name": "Turbidity",
            "domain": "water_quality",
            "unitId": str(unitId),
            "methodName": "LabTurbidity",
            "methodVersion": "2.1",
            "criteriaVersion": "criteria-2026-01",
        },
    )
    assert response.status_code == 201, response.text
    ids["indicator"] = response.json()["id"]

    response = client.post(
        f"/api/v1/verification/measurements/{ids['indicator']}",
        headers=headers,
        json={
            "organisationId": org,
            "measuredAt": NOW.isoformat(),
            "qualifier": "exact",
            "unitId": str(unitId),
            "methodName": "LabTurbidity",
            "methodVersion": "2.1",
            "value": 12.5,
            "caseId": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 201, response.text
    ids["measurement"] = response.json()["id"]

    response = client.post(
        "/api/v1/verification/assessments",
        headers=headers,
        json={
            "organisationId": org,
            "interventionId": str(uuid.uuid4()),
            "baselineMeasurementIds": [ids["measurement"]],
            "followUpMeasurementIds": [str(uuid.uuid4())],
            "comparisonMethod": "Matched site comparison",
            "baselineValues": [10.0, 11.0],
            "followUpValues": [4.0, 5.0],
            "direction": "decrease",
            "minimumDetectableChange": 1.0,
            "criteriaVersion": "criteria-2026-01",
        },
    )
    assert response.status_code == 201, response.text
    ids["verification"] = response.json()["id"]

    authority = create_temp_user(
        dbSession, memberships=[(orgId, Role.ORGANISATION_ADMIN)]
    )
    response = client.post(
        "/api/v1/verification/publications",
        headers=headers,
        json={
            "organisationId": org,
            "specialistApproverUserId": str(specialistApproverUserId),
            "authorityApproverUserId": str(authority.id),
            "publishedText": "Turbidity improved at the monitored site.",
            "verificationAssessmentId": ids["verification"],
        },
    )
    assert response.status_code == 201, response.text
    ids["publication"] = response.json()["id"]
    return ids


def _child_lists(ids: dict[str, str]) -> tuple[tuple[str, str, str], ...]:
    """Return (parent key, path, child id field) for the three nested lists."""
    return (
        ("run", f"/api/v1/intelligence/analyses/{ids['run']}/outputs", "analysisRunId"),
        ("dataset", f"/api/v1/catalogue/datasets/{ids['dataset']}/versions", "datasetId"),
        (
            "intervention",
            f"/api/v1/interventions/interventions/{ids['intervention']}/milestones",
            "interventionId",
        ),
    )


def test_read_apis_return_own_org_records_with_camel_case_page(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    """A permitted caller sees their own records and the standard page envelope."""
    orgId, headers, actorId = _actor(dbSession, authProvider)
    otherOrgId, otherHeaders, otherActorId = _actor(dbSession, authProvider)
    unitId = _temp_unit(dbSession)
    ownIds = _seed(client, dbSession, storageProvider, headers, orgId, unitId, actorId)
    _seed(client, dbSession, storageProvider, otherHeaders, otherOrgId, unitId, otherActorId)

    for name, path in TOP_LEVEL_LISTS:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, (name, response.text)
        body = response.json()
        assert "nextCursor" in body and "hasMore" in body, name
        assert len(body["items"]) == 1, name
        assert all(item["organisationId"] == str(orgId) for item in body["items"]), name

    for parentKey, path, childField in _child_lists(ownIds):
        response = client.get(path, headers=headers)
        assert response.status_code == 200, (parentKey, response.text)
        body = response.json()
        assert len(body["items"]) == 1, parentKey
        assert body["items"][0][childField] == ownIds[parentKey], parentKey


def test_read_apis_let_system_admin_see_all_organisations(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    """A system admin sees every organisation and may still filter by one."""
    orgId, headers, actorId = _actor(dbSession, authProvider)
    otherOrgId, otherHeaders, otherActorId = _actor(dbSession, authProvider)
    unitId = _temp_unit(dbSession)
    idsA = _seed(client, dbSession, storageProvider, headers, orgId, unitId, actorId)
    idsB = _seed(client, dbSession, storageProvider, otherHeaders, otherOrgId, unitId, otherActorId)
    adminHeaders = auth_headers(
        authProvider,
        create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN),
    )

    for name, path in TOP_LEVEL_LISTS:
        response = client.get(path, headers=adminHeaders)
        assert response.status_code == 200, (name, response.text)
        assert len(response.json()["items"]) == 2, name

        filtered = client.get(path, headers=adminHeaders, params={"organisationId": str(orgId)})
        assert filtered.status_code == 200, (name, filtered.text)
        assert [item["organisationId"] for item in filtered.json()["items"]] == [str(orgId)], name

    for parentKey, path, childField in _child_lists(idsB):
        response = client.get(path, headers=adminHeaders)
        assert response.status_code == 200, (parentKey, response.text)
        assert response.json()["items"][0][childField] == idsB[parentKey], parentKey
    assert _child_lists(idsA)[0][1] != _child_lists(idsB)[0][1]


def test_read_apis_refuse_cross_org_filter_and_missing_permission(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    """Cross-organisation filters and roles without the gate are refused server-side."""
    orgId, headers, actorId = _actor(dbSession, authProvider)
    otherOrgId, otherHeaders, otherActorId = _actor(dbSession, authProvider)
    unitId = _temp_unit(dbSession)
    _seed(client, dbSession, storageProvider, headers, orgId, unitId, actorId)
    _seed(client, dbSession, storageProvider, otherHeaders, otherOrgId, unitId, otherActorId)

    unauthorisedId, unauthorisedHeaders, _ = _actor(
        dbSession, authProvider, Role.REGISTERED_CONTRIBUTOR
    )
    assert unauthorisedId != orgId

    for name, path in TOP_LEVEL_LISTS:
        crossOrg = client.get(
            path, headers=headers, params={"organisationId": str(otherOrgId)}
        )
        assert crossOrg.status_code == 403, (name, crossOrg.text)
        assert crossOrg.json()["code"] == "FORBIDDEN", name

        denied = client.get(path, headers=unauthorisedHeaders)
        assert denied.status_code == 403, (name, denied.text)

        anonymous = client.get(path)
        assert anonymous.status_code == 401, (name, anonymous.text)


def test_read_apis_hide_out_of_scope_child_parents(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    """Child lists return 404 for a parent in another organisation."""
    orgId, headers, actorId = _actor(dbSession, authProvider)
    otherOrgId, otherHeaders, otherActorId = _actor(dbSession, authProvider)
    unitId = _temp_unit(dbSession)
    otherIds = _seed(
        client, dbSession, storageProvider, otherHeaders, otherOrgId, unitId, otherActorId
    )
    _seed(client, dbSession, storageProvider, headers, orgId, unitId, actorId)

    for parentKey, path, _ in _child_lists(otherIds):
        response = client.get(path, headers=headers)
        assert response.status_code == 404, (parentKey, response.text)


def test_read_api_pagination_uses_next_cursor(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    """A bounded first page and its opaque cursor return the remaining record."""
    orgId, headers, actorId = _actor(dbSession, authProvider)
    unitId = _temp_unit(dbSession)
    first = _seed(client, dbSession, storageProvider, headers, orgId, unitId, actorId)["dataset"]
    second = client.post(
        "/api/v1/catalogue/datasets",
        headers=headers,
        json={
            "organisationId": str(orgId),
            "name": f"Second baseline {uuid.uuid4().hex[:6]}",
            "owner": "EcoWatch",
            "licence": "CC-BY-4.0",
            "attribution": "EcoWatch field team",
            "permittedUse": "Environmental monitoring",
            "crs": "EPSG:4326",
        },
    )
    assert second.status_code == 201, second.text

    pageOne = client.get(
        "/api/v1/catalogue/datasets", headers=headers, params={"limit": 1}
    )
    assert pageOne.status_code == 200, pageOne.text
    bodyOne = pageOne.json()
    assert len(bodyOne["items"]) == 1
    assert bodyOne["hasMore"] is True
    assert bodyOne["nextCursor"]

    pageTwo = client.get(
        "/api/v1/catalogue/datasets",
        headers=headers,
        params={"limit": 1, "cursor": bodyOne["nextCursor"]},
    )
    assert pageTwo.status_code == 200, pageTwo.text
    bodyTwo = pageTwo.json()
    assert len(bodyTwo["items"]) == 1
    assert {bodyOne["items"][0]["id"], bodyTwo["items"][0]["id"]} == {
        first,
        second.json()["id"],
    }
    assert bodyTwo["hasMore"] is False
    assert bodyTwo["nextCursor"] is None

    invalid = client.get(
        "/api/v1/catalogue/datasets", headers=headers, params={"cursor": "not-a-cursor"}
    )
    assert invalid.status_code == 400, invalid.text


def test_reviewer_can_read_intelligence_without_write_permission(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    """ADR-040: reviewer holds INTELLIGENCE_READ without INTELLIGENCE_WRITE."""
    orgId, reviewerHeaders, _ = _actor(
        dbSession, authProvider, Role.REVIEWER
    )

    readResp = client.get("/api/v1/intelligence/analyses", headers=reviewerHeaders)
    assert readResp.status_code == 200, readResp.text

    writeResp = client.post(
        "/api/v1/intelligence/entities",
        headers=reviewerHeaders,
        json={
            "organisationId": str(orgId),
            "entityType": "site",
            "name": "Blocked Write Site",
        },
    )
    assert writeResp.status_code == 403, writeResp.text
