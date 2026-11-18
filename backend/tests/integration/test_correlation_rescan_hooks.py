"""Corrections and evidence uploads requeue a correlation scan."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.collection.schemas import CreateObservationRequest
from ecowatch.modules.collection.service import CollectionService
from ecowatch.modules.correlation.service import SCAN_JOB_TYPE
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.identity.permissions import Principal, Role
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.observations.schemas import CreateCorrectionRequest
from ecowatch.modules.observations.service import ObservationService
from tests.conftest import (
    create_temp_org,
    create_temp_user,
    make_jpeg_with_exif_bytes,
)


def _staff_principal(dbSession: Session, organisationId: uuid.UUID) -> Principal:
    user = create_temp_user(
        dbSession, memberships=[(organisationId, Role.REVIEWER)]
    )
    return Principal(
        userId=user.id,
        memberships=((organisationId, Role.REVIEWER),),
        isAuthenticated=True,
    )


def _scan_jobs(dbSession: Session) -> list[ProcessingJob]:
    return list(
        dbSession.scalars(
            select(ProcessingJob).where(ProcessingJob.jobType == SCAN_JOB_TYPE)
        ).all()
    )


def test_correction_queues_another_scan(dbSession: Session, testSettings: Settings) -> None:
    org = create_temp_org(dbSession)
    receipt, _ = CollectionService(dbSession).submit_observation(
        Principal(),
        CreateObservationRequest(
            idempotencyKey=uuid.uuid4(),
            organisationId=org.id,
            observationType="water_pollution",
            description="oily sheen at the river bend",
        ),
        settings=testSettings,
        clientIp="127.0.0.1",
    )
    before = len(_scan_jobs(dbSession))
    assert before == 1

    ObservationService(dbSession).correct_observation(
        _staff_principal(dbSession, org.id),
        receipt.observationId,
        CreateCorrectionRequest(reason="Typo fix", description="oily sheen downstream"),
        settings=testSettings,
    )

    jobs = _scan_jobs(dbSession)
    assert len(jobs) == before + 1
    assert jobs[-1].status == JobStatus.PENDING.value
    assert jobs[-1].payload == {"observationId": str(receipt.observationId)}
    assert jobs[-1].maxAttempts == testSettings.workerMaxAttempts


def test_evidence_upload_queues_another_scan(
    dbSession: Session, testSettings: Settings, storageProvider: StorageProvider
) -> None:
    org = create_temp_org(dbSession)
    receipt, _ = CollectionService(dbSession).submit_observation(
        Principal(),
        CreateObservationRequest(
            idempotencyKey=uuid.uuid4(),
            organisationId=org.id,
            observationType="water_pollution",
            description="oily sheen at the river bend",
        ),
        settings=testSettings,
        clientIp="127.0.0.1",
    )
    before = len(_scan_jobs(dbSession))
    assert before == 1

    EvidenceService(dbSession, storageProvider).upload_evidence(
        _staff_principal(dbSession, org.id),
        receipt.observationId,
        rawBytes=make_jpeg_with_exif_bytes(),
        filename="river_sample.jpg",
        declaredMimeType="image/jpeg",
        settings=testSettings,
    )

    jobs = _scan_jobs(dbSession)
    assert len(jobs) == before + 1
    assert jobs[-1].status == JobStatus.PENDING.value
    assert jobs[-1].payload == {"observationId": str(receipt.observationId)}
    assert jobs[-1].maxAttempts == testSettings.workerMaxAttempts
