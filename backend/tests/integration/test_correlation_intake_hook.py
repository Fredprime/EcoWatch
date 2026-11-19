"""Intake queues a correlation scan, and the worker turns it into a review aid."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.collection.schemas import CreateObservationRequest
from ecowatch.modules.collection.service import CollectionService
from ecowatch.modules.correlation.models import CorrelationCluster
from ecowatch.modules.correlation.service import SCAN_JOB_TYPE
from ecowatch.modules.identity.permissions import Principal
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.jobs.worker import run_once
from tests.conftest import create_temp_org


def test_new_observation_queues_one_scan_and_a_replay_queues_no_more(
    dbSession: Session, testSettings: Settings
) -> None:
    """Scoring stays out of the intake request, and retrying a receipt is free."""
    org = create_temp_org(dbSession)
    payload = CreateObservationRequest(
        idempotencyKey=uuid.uuid4(),
        organisationId=org.id,
        observationType="water_pollution",
        description="oily sheen at the river bend",
    )
    service = CollectionService(dbSession)

    receipt, replayed = service.submit_observation(
        Principal(), payload, settings=testSettings, clientIp="127.0.0.1"
    )
    assert replayed is False

    jobs = list(
        dbSession.scalars(
            select(ProcessingJob).where(ProcessingJob.jobType == SCAN_JOB_TYPE)
        ).all()
    )
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.PENDING.value
    assert jobs[0].payload == {"observationId": str(receipt.observationId)}
    assert jobs[0].maxAttempts == testSettings.workerMaxAttempts

    replayReceipt, replayed = service.submit_observation(
        Principal(), payload, settings=testSettings, clientIp="127.0.0.1"
    )
    assert replayed is True
    assert replayReceipt.observationId == receipt.observationId
    assert len(
        list(
            dbSession.scalars(
                select(ProcessingJob).where(ProcessingJob.jobType == SCAN_JOB_TYPE)
            ).all()
        )
    ) == 1


def test_worker_scans_the_queued_observation(
    dbSession: Session, testSettings: Settings, storageProvider: StorageProvider
) -> None:
    """The job the enqueue wrote is the job the worker knows how to run."""
    org = create_temp_org(dbSession)
    receipt, _ = CollectionService(dbSession).submit_observation(
        Principal(),
        CreateObservationRequest(
            idempotencyKey=uuid.uuid4(),
            organisationId=org.id,
            observationType="noise",
            description="generator running all night",
        ),
        settings=testSettings,
        clientIp="127.0.0.1",
    )

    assert run_once(dbSession, storageProvider) == 1
    job = dbSession.scalar(select(ProcessingJob).where(ProcessingJob.jobType == SCAN_JOB_TYPE))
    assert job is not None
    assert job.status == JobStatus.PROCESSED.value
    assert job.lastError is None

    # A scanned report has a provisional, staff-only home even with no match.
    clusters = list(dbSession.scalars(select(CorrelationCluster)).all())
    assert len(clusters) == 1
    assert clusters[0].organisationId == org.id
