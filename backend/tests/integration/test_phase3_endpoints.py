"""End-to-end Phase 3 API endpoint tests using isolated temporary records."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.identity.permissions import Role
from ecowatch.modules.intelligence.models import AnalysisRun
from ecowatch.modules.observations.models import Unit
from tests.conftest import auth_headers, create_temp_org, create_temp_user

NOW = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)


def _authenticate(
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    role: Role = Role.ENVIRONMENTAL_SPECIALIST,
) -> tuple[uuid.UUID, dict[str, str]]:
    """Create a temporary organisation and authenticated principal for one test."""
    org = create_temp_org(dbSession)
    user = create_temp_user(dbSession, memberships=[(org.id, role)])
    return org.id, auth_headers(authProvider, user)


def _create_temp_unit(dbSession: Session) -> uuid.UUID:
    """Create a temporary controlled unit for measurement tests."""
    unit = Unit(symbol=f"NTU-{uuid.uuid4().hex[:8]}", name="Turbidity", dimension="turbidity")
    dbSession.add(unit)
    dbSession.commit()
    return unit.id


def test_catalogue_endpoints_create_dataset_and_version(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    response = client.post(
        "/api/v1/catalogue/datasets",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "name": "River turbidity baseline",
            "owner": "EcoWatch",
            "licence": "CC-BY-4.0",
            "attribution": "EcoWatch field team",
            "permittedUse": "Environmental monitoring",
            "crs": "EPSG:4326",
            "coverageStartAt": NOW.isoformat(),
            "coverageEndAt": LATER.isoformat(),
            "coverageGeometry": "POINT(0.1 5.6)",
        },
    )
    assert response.status_code == 201, response.text
    dataset = response.json()
    assert dataset["licence"] == "CC-BY-4.0"
    assert dataset["coverageGeometry"] == "POINT(0.1 5.6)"

    version = client.post(
        f"/api/v1/catalogue/datasets/{dataset['id']}/versions",
        headers=headers,
        json={
            "organisationId": str(organisationId),
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
    assert version.status_code == 201, version.text
    assert version.json()["versionLabel"] == "v1"


def test_intelligence_endpoints_entity_relationship_analysis_and_gate(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    base = "/api/v1/intelligence"

    entity = client.post(
        f"{base}/entities",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "entityType": "catchment",
            "name": "Upper catchment",
            "geometry": "POLYGON((0 0, 1 0, 1 1, 0 0))",
        },
    )
    assert entity.status_code == 201, entity.text

    relationship = client.post(
        f"{base}/relationships",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "relationshipType": "upstream_downstream",
            "evidenceSummary": "Observations follow the inferred flow direction.",
            "uncertainty": "medium",
            "uncertaintyNote": "Flow direction is inferred from a coarse model.",
            "alternativeExplanations": "A separate source may contribute.",
            "methodName": "CatchmentPathway",
            "methodVersion": "1.0",
            "fromEntityId": entity.json()["id"],
            "toObservationId": str(uuid.uuid4()),
        },
    )
    assert relationship.status_code == 201, relationship.text
    relationshipId = relationship.json()["id"]
    assert relationship.json()["reviewState"] == "proposed"

    reviewed = client.post(
        f"{base}/relationships/{relationshipId}/review",
        headers=headers,
        json={"organisationId": str(organisationId), "reviewState": "reviewed"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewState"] == "reviewed"

    analysis = client.post(
        f"{base}/analyses",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "question": "Did bare soil increase?",
            "analysisType": "land_cover_change",
            "methodName": "NDVIThreshold",
            "methodVersion": "1.0",
            "inputDatasetVersionIds": [str(uuid.uuid4())],
            "crs": "EPSG:4326",
            "parameters": {"threshold": 0.2},
            "limitations": "Cloud cover in one month.",
        },
    )
    assert analysis.status_code == 202, analysis.text
    runId = analysis.json()["id"]
    assert analysis.json()["status"] == "queued"

    run = dbSession.get(AnalysisRun, uuid.UUID(runId))
    assert run is not None
    run.status = "running"
    dbSession.commit()

    output = client.post(
        f"{base}/analyses/{runId}/outputs",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "outputType": "map",
            "summary": "Bare soil estimate for the catchment.",
            "limitations": "Cloud cover limits the comparison.",
        },
    )
    assert output.status_code == 201, output.text
    assert output.json()["interpretationState"] == "pending_review"

    blocked = client.post(
        f"{base}/predictions/check",
        headers=headers,
        json={"organisationId": str(organisationId), "targetDefined": False},
    )
    assert blocked.status_code in {400, 409}, blocked.text
    assert blocked.json()["code"] == "PREDICTION_BLOCKED"


def test_prioritisation_endpoints_assessment_and_decision(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    base = "/api/v1/prioritisation"

    assessment = client.post(
        f"{base}/assessments",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "caseId": str(uuid.uuid4()),
            "methodName": "TransparentFactors",
            "methodVersion": "1.0",
            "factors": {"magnitude": "large", "extent": None},
            "compositeRank": 2.0,
            "rankingMethodRef": "docs/prioritisation-method.md",
            "rankIsNotSeverity": True,
        },
    )
    assert assessment.status_code == 201, assessment.text
    body = assessment.json()
    assert "extent" in body["missingInputs"]
    assert body["rankIsNotSeverity"] is True

    decided = client.post(
        f"{base}/assessments/{body['id']}/decision",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "decision": "priority_set",
            "rationale": "Evidence quality and magnitude justify review first.",
        },
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["decision"] == "priority_set"


def test_interventions_endpoints_lifecycle(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    base = "/api/v1/interventions"
    userId = str(uuid.uuid4())

    intervention = client.post(
        f"{base}/interventions",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "caseId": str(uuid.uuid4()),
            "objective": "Reduce sediment entering the catchment.",
            "responsibleOrganisationId": str(organisationId),
            "authorisedLeadUserId": userId,
            "location": "POINT(0.2 5.7)",
        },
    )
    assert intervention.status_code == 201, intervention.text
    interventionId = intervention.json()["id"]

    milestone = client.post(
        f"{base}/interventions/{interventionId}/milestones",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "name": "Install sediment traps",
            "plannedAt": NOW.isoformat(),
        },
    )
    assert milestone.status_code == 201, milestone.text
    milestoneId = milestone.json()["id"]

    completed = client.post(
        f"{base}/milestones/{milestoneId}/complete",
        headers=headers,
        json={"organisationId": str(organisationId), "evidenceAssetIds": [str(uuid.uuid4())]},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"

    finalStatus = None
    for target in ("approved", "scheduled", "in_progress", "activity_completed"):
        transitioned = client.post(
            f"{base}/interventions/{interventionId}/transition",
            headers=headers,
            json={
                "organisationId": str(organisationId),
                "targetStatus": target,
                "rationale": "Governed progression through the intervention lifecycle.",
            },
        )
        assert transitioned.status_code == 200, transitioned.text
        finalStatus = transitioned.json()

    assert finalStatus["status"] == "activity_completed"
    assert finalStatus["verificationAssessmentId"] is None


def test_verification_endpoints_measurements_assessment_and_publication(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    unitId = _create_temp_unit(dbSession)
    base = "/api/v1/verification"

    indicator = client.post(
        f"{base}/indicators",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "code": f"TURB-{uuid.uuid4().hex[:6]}",
            "name": "Turbidity",
            "domain": "water_quality",
            "unitId": str(unitId),
            "methodName": "LabTurbidity",
            "methodVersion": "2.1",
            "criteriaVersion": "criteria-2026-01",
        },
    )
    assert indicator.status_code == 201, indicator.text
    indicatorId = indicator.json()["id"]

    measurement = client.post(
        f"{base}/measurements/{indicatorId}",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "measuredAt": NOW.isoformat(),
            "qualifier": "exact",
            "unitId": str(unitId),
            "methodName": "LabTurbidity",
            "methodVersion": "2.1",
            "value": 12.5,
            "caseId": str(uuid.uuid4()),
        },
    )
    assert measurement.status_code == 201, measurement.text
    assert measurement.json()["value"] == 12.5

    assessment = client.post(
        f"{base}/assessments",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "interventionId": str(uuid.uuid4()),
            "baselineMeasurementIds": [measurement.json()["id"]],
            "followUpMeasurementIds": [str(uuid.uuid4())],
            "comparisonMethod": "Matched site comparison",
            "baselineValues": [10.0, 11.0],
            "followUpValues": [4.0, 5.0],
            "direction": "decrease",
            "minimumDetectableChange": 1.0,
            "criteriaVersion": "criteria-2026-01",
        },
    )
    assert assessment.status_code == 201, assessment.text
    assessmentBody = assessment.json()
    assert assessmentBody["conclusion"] == "improvement"
    assert assessmentBody["conclusion"] != "recovery_verified"

    finalised = client.post(
        f"{base}/assessments/{assessmentBody['id']}/finalise",
        headers=headers,
        json={"organisationId": str(organisationId)},
    )
    assert finalised.status_code == 200, finalised.text
    assert finalised.json()["status"] == "final"

    recovered = client.post(
        f"{base}/assessments/{assessmentBody['id']}/recovery",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "criteriaVersion": "criteria-2026-01",
            "criteriaApproved": True,
            "comparisonMethod": "Matched site comparison",
            "uncertaintyDocumented": "95% interval recorded.",
            "confoundersDocumented": "Rainfall considered.",
            "seasonalContextDocumented": "Dry season matched.",
        },
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["conclusion"] == "recovery_verified"

    publication = client.post(
        f"{base}/publications",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "publishedText": "Turbidity improved at the monitored site.",
            "verificationAssessmentId": assessmentBody["id"],
        },
    )
    assert publication.status_code == 201, publication.text
    publicationId = publication.json()["id"]

    retracted = client.post(
        f"{base}/publications/{publicationId}/retract",
        headers=headers,
        json={"organisationId": str(organisationId), "reason": "Superseded by corrected data."},
    )
    assert retracted.status_code == 200, retracted.text
    assert retracted.json()["retractedAt"] is not None
    assert retracted.json()["publishedText"] == "Turbidity improved at the monitored site."


def test_phase3_endpoints_deny_missing_permission(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider, Role.REGISTERED_CONTRIBUTOR)
    response = client.post(
        "/api/v1/catalogue/datasets",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "name": "Unauthorised dataset",
            "owner": "EcoWatch",
            "licence": "CC-BY-4.0",
            "attribution": "EcoWatch field team",
            "permittedUse": "Environmental monitoring",
            "crs": "EPSG:4326",
        },
    )
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "FORBIDDEN"
