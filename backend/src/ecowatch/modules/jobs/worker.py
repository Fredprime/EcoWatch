"""Synchronous job runner and async background worker loop for processing_jobs."""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from ecowatch.core.models import utc_now
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.jobs.repository import JobsRepository, claim_next_batch

_logger = logging.getLogger("ecowatch.worker")


def _execute_job(session: Session, storage: StorageProvider, job: ProcessingJob) -> None:
    """Dispatch a single claimed job to its domain handler."""
    if job.jobType == "evidence.scan_and_derive":
        from ecowatch.modules.evidence.service import EvidenceService

        assetId = uuid.UUID(str(job.payload["assetId"]))
        EvidenceService(session, storage).process_scan_and_derive(assetId)
        return
    raise ValueError(f"Unsupported job type: {job.jobType}")


def run_once(
    session: Session,
    storage: StorageProvider,
    *,
    batchSize: int = 5,
    maxAttempts: int | None = None,
    now: datetime | None = None,
) -> int:
    """Claim and process up to batchSize eligible jobs synchronously; return claimed count."""
    jobs = claim_next_batch(session, batchSize, now=now)
    if not jobs:
        return 0
    session.commit()

    repo = JobsRepository(session)
    for claimed in jobs:
        job = repo.get_by_id(claimed.id)
        if job is None:
            continue
        try:
            _execute_job(session, storage, job)
            job.status = JobStatus.PROCESSED.value
            job.completedAt = utc_now()
            job.lastError = None
            session.commit()
        except Exception as exc:
            session.rollback()
            failedJob = repo.get_by_id(claimed.id)
            if failedJob is None:
                continue
            effectiveLimit = (
                maxAttempts if maxAttempts is not None else failedJob.maxAttempts
            )
            failedJob.lastError = f"{type(exc).__name__}: {str(exc)[:500]}"
            currentTime = utc_now()
            if failedJob.attempts >= effectiveLimit:
                failedJob.status = JobStatus.DEAD.value
                failedJob.completedAt = currentTime
            else:
                backoff = min(300.0, float(2 ** min(failedJob.attempts, 8)))
                jitter = random.uniform(0.0, 1.0)
                failedJob.status = JobStatus.FAILED.value
                failedJob.availableAt = currentTime + timedelta(seconds=backoff + jitter)
            session.commit()
            _logger.warning(
                "job_failed",
                extra={
                    "structured": {
                        "jobId": str(failedJob.id),
                        "jobType": failedJob.jobType,
                        "errorCode": type(exc).__name__,
                    }
                },
            )
    return len(jobs)


async def worker_loop(
    sessionFactory: sessionmaker[Session],
    storage: StorageProvider,
    *,
    pollIntervalSeconds: float = 2.0,
    batchSize: int = 5,
    maxAttempts: int = 5,
    stopEvent: asyncio.Event | None = None,
) -> None:
    """Bounded async polling loop running run_once until cancelled or stopped."""
    while stopEvent is None or not stopEvent.is_set():
        def _run_batch() -> int:
            with sessionFactory() as session:
                return run_once(
                    session,
                    storage,
                    batchSize=batchSize,
                    maxAttempts=maxAttempts,
                )

        processed = await asyncio.to_thread(_run_batch)
        if processed > 0:
            continue
        if stopEvent is None:
            await asyncio.sleep(pollIntervalSeconds)
        else:
            try:
                await asyncio.wait_for(stopEvent.wait(), timeout=pollIntervalSeconds)
            except TimeoutError:
                continue
