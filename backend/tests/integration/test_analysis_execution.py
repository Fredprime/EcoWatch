"""Real analysis.run execution over stored dataset records, with honest failures."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.catalogue.models import Dataset, DatasetVersion
from ecowatch.modules.identity.permissions import Role
from ecowatch.modules.intelligence import rules
from ecowatch.modules.intelligence.models import AnalysisOutput, AnalysisRun
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.jobs.worker import run_once
from tests.conftest import auth_headers, create_temp_org, create_temp_user

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
CSV_DATA = b"site,reading,note\nA,1.5,present\nB,,missing\nC,3.5,ok\n"


def _authenticate(
    dbSession: Session, authProvider: LocalTokenAuthProvider
) -> tuple[uuid.UUID, dict[str, str]]:
    org = create_temp_org(dbSession)
    user = create_temp_user(dbSession, memberships=[(org.id, Role.ENVIRONMENTAL_SPECIALIST)])
    return org.id, auth_headers(authProvider, user)


def _make_version(
    dbSession: Session,
    storageProvider: StorageProvider,
    organisationId: uuid.UUID,
    *,
    data: bytes | None = CSV_DATA,
    withStorageKey: bool = True,
) -> uuid.UUID:
    dataset = Dataset(
        organisationId=organisationId,
        name=f"ds-{uuid.uuid4().hex[:8]}",
        owner="EcoWatch",
        licence="CC-BY-4.0",
        attribution="EcoWatch",
        permittedUse="Monitoring",
        crs="EPSG:4326",
    )
    dbSession.add(dataset)
    dbSession.flush()
    key = f"datasets/{uuid.uuid4().hex}.csv" if withStorageKey else None
    version = DatasetVersion(
        datasetId=dataset.id,
        versionLabel="v1",
        sourceAcquisitionAt=NOW,
        resolution="10m",
        crs="EPSG:4326",
        method="Field sampling",
        licenceSnapshot="CC-BY-4.0",
        attributionSnapshot="EcoWatch",
        permittedUseSnapshot="Monitoring",
        storageKey=key,
    )
    dbSession.add(version)
    dbSession.flush()
    if key is not None and data is not None:
        storageProvider.put_bytes(key, data)
    dbSession.commit()
    return version.id


def _queue_run(
    client: TestClient,
    headers: dict[str, str],
    organisationId: uuid.UUID,
    versionIds: list[uuid.UUID],
) -> uuid.UUID:
    response = client.post(
        "/api/v1/intelligence/analyses",
        headers=headers,
        json={
            "organisationId": str(organisationId),
            "question": "What do the stored readings show?",
            "analysisType": "water_quality_comparison",
            "methodName": "NDVIThreshold",
            "methodVersion": "1.0",
            "inputDatasetVersionIds": [str(value) for value in versionIds],
            "crs": "EPSG:4326",
            "parameters": {},
            "limitations": "Single sampled season.",
        },
    )
    assert response.status_code == 202, response.text
    return uuid.UUID(response.json()["id"])


def _get_run(dbSession: Session, runId: uuid.UUID) -> AnalysisRun:
    dbSession.expire_all()
    run = dbSession.get(AnalysisRun, runId)
    assert run is not None
    return run


def _outputs_for(dbSession: Session, runId: uuid.UUID) -> list[AnalysisOutput]:
    return list(
        dbSession.scalars(
            select(AnalysisOutput).where(AnalysisOutput.analysisRunId == runId)
        ).all()
    )


def test_execution_writes_deterministic_interpretation_free_summary(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    versionId = _make_version(dbSession, storageProvider, organisationId)
    runId = _queue_run(client, headers, organisationId, [versionId])

    assert run_once(dbSession, storageProvider) == 1

    run = _get_run(dbSession, runId)
    assert run.status == "succeeded"
    assert run.completedAt is not None
    assert run.failureReason is None

    outputs = _outputs_for(dbSession, runId)
    assert len(outputs) == 1
    output = outputs[0]
    assert output.outputType == "table"
    assert output.isDerived is True
    assert output.derivedFromObservationIds == []
    assert output.interpretationState == "pending_review"
    assert "Single sampled season." in output.limitations
    assert rules.SUMMARY_LIMITATIONS_CAVEAT in output.limitations

    summary = json.loads(output.summary)
    assert summary["computationMethod"] == {
        "name": rules.SUMMARY_METHOD_NAME,
        "version": rules.SUMMARY_METHOD_VERSION,
    }
    assert summary["declaredMethod"] == {"name": "NDVIThreshold", "version": "1.0"}
    assert summary["recordCount"] == 3
    assert summary["columnCount"] == 3
    assert summary["qualityFlags"] == {
        "missingValuesPresent": True,
        "numericValuesPresent": True,
    }
    reading = summary["columns"]["reading"]
    assert reading["count"] == 2
    assert reading["missingCount"] == 1
    assert reading["numericCount"] == 2
    assert reading["min"] == 1.5
    assert reading["max"] == 3.5
    assert reading["mean"] == 2.5

    job = dbSession.scalar(
        select(ProcessingJob).where(ProcessingJob.jobType == "analysis.run")
    )
    assert job is not None
    assert job.status == JobStatus.PROCESSED.value
    assert job.lastError is None


def test_execution_succeeds_repeatedly_without_duplicate_outputs(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    versionId = _make_version(dbSession, storageProvider, organisationId)
    runId = _queue_run(client, headers, organisationId, [versionId])

    from ecowatch.modules.intelligence.service import IntelligenceService

    service = IntelligenceService(dbSession)
    service.execute_analysis_run(runId, storageProvider)
    firstSummary = _outputs_for(dbSession, runId)[0].summary
    service.execute_analysis_run(runId, storageProvider)

    assert len(_outputs_for(dbSession, runId)) == 1
    assert _outputs_for(dbSession, runId)[0].summary == firstSummary


def test_summary_builder_is_deterministic_and_has_no_declarative_fields() -> None:
    records: list[dict[str, Any]] = [
        {"b": "2", "a": 1},
        {"a": None, "b": 3},
    ]
    first = rules.build_stored_value_summary(
        records, declaredMethodName="M", declaredMethodVersion="1"
    )
    second = rules.build_stored_value_summary(
        records, declaredMethodName="M", declaredMethodVersion="1"
    )
    assert first == second
    assert first["recordCount"] == 2
    assert first["columns"]["a"]["missingCount"] == 1
    assert first["columns"]["b"]["mean"] == 2.5
    assert not {"source", "causation", "harm", "severity", "verification"} & set(first)


def test_execution_fails_when_input_version_is_missing(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    runId = _queue_run(client, headers, organisationId, [uuid.uuid4()])

    assert run_once(dbSession, storageProvider) == 1

    run = _get_run(dbSession, runId)
    assert run.status == "failed"
    assert run.failureReason and "unavailable or out of scope" in run.failureReason
    assert run.completedAt is None
    assert _outputs_for(dbSession, runId) == []

    job = dbSession.scalar(
        select(ProcessingJob).where(ProcessingJob.jobType == "analysis.run")
    )
    assert job is not None
    assert job.status == JobStatus.FAILED.value
    assert job.lastError and "unavailable or out of scope" in job.lastError


@pytest.mark.parametrize(
    ("versionOptions", "expectedReason"),
    [
        ({"withStorageKey": False}, "no stored data"),
        ({"data": b""}, "no content"),
        ({"data": b'{"records": "not-a-list"}'}, "could not be parsed"),
    ],
)
def test_execution_fails_on_unusable_stored_data(
    versionOptions: dict[str, Any],
    expectedReason: str,
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    storageProvider: StorageProvider,
) -> None:
    organisationId, headers = _authenticate(dbSession, authProvider)
    versionId = _make_version(dbSession, storageProvider, organisationId, **versionOptions)
    runId = _queue_run(client, headers, organisationId, [versionId])

    assert run_once(dbSession, storageProvider) == 1

    run = _get_run(dbSession, runId)
    assert run.status == "failed"
    assert run.failureReason and expectedReason in run.failureReason
    assert _outputs_for(dbSession, runId) == []
