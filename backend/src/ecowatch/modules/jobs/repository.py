"""Repository for enqueuing, claiming, listing, and summarizing processing jobs."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ecowatch.core.models import utc_now
from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob


def claim_next_batch(
    session: Session, batchSize: int, *, now: datetime | None = None
) -> list[ProcessingJob]:
    """Claim up to batchSize eligible jobs using SKIP LOCKED on PostgreSQL."""
    current = now or utc_now()
    stmt = (
        select(ProcessingJob)
        .where(
            ProcessingJob.status.in_((JobStatus.PENDING.value, JobStatus.FAILED.value)),
            ProcessingJob.availableAt <= current,
        )
        .order_by(ProcessingJob.availableAt.asc(), ProcessingJob.createdAt.asc())
        .limit(batchSize)
    )
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    jobs = list(session.scalars(stmt).all())
    for job in jobs:
        job.status = JobStatus.PROCESSING.value
        job.startedAt = current
        job.attempts += 1
    if jobs:
        session.flush()
    return jobs


class JobsRepository:
    """Data-access operations for processing_jobs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, jobId: uuid.UUID) -> ProcessingJob | None:
        return self._session.get(ProcessingJob, jobId)

    def enqueue(
        self,
        jobType: str,
        payload: dict[str, Any],
        *,
        maxAttempts: int = 5,
        availableAt: datetime | None = None,
    ) -> ProcessingJob:
        """Insert a pending job within the caller's active transaction."""
        job = ProcessingJob(
            jobType=jobType,
            payload=dict(payload),
            status=JobStatus.PENDING.value,
            attempts=0,
            maxAttempts=maxAttempts,
            availableAt=availableAt or utc_now(),
        )
        self._session.add(job)
        self._session.flush()
        return job

    def claim_next_batch(
        self, batchSize: int, *, now: datetime | None = None
    ) -> list[ProcessingJob]:
        """Claim the next batch of eligible pending/failed jobs."""
        return claim_next_batch(self._session, batchSize, now=now)

    def list_jobs(
        self,
        *,
        statusFilter: JobStatus | None = None,
        jobType: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[ProcessingJob], str | None, bool]:
        """List processing jobs newest first with keyset cursor pagination."""
        stmt = select(ProcessingJob)
        if statusFilter is not None:
            stmt = stmt.where(ProcessingJob.status == statusFilter.value)
        if jobType is not None:
            stmt = stmt.where(ProcessingJob.jobType == jobType)
        return paginate_descending(
            self._session,
            stmt,
            timeCol=ProcessingJob.createdAt,
            idCol=ProcessingJob.id,
            cursor=cursor,
            limit=limit,
        )

    def summarize_counts(self) -> list[tuple[str, str, int]]:
        """Aggregate job counts grouped by (jobType, status)."""
        stmt = select(
            ProcessingJob.jobType,
            ProcessingJob.status,
            func.count(ProcessingJob.id),
        ).group_by(ProcessingJob.jobType, ProcessingJob.status)
        return [
            (str(row[0]), str(row[1]), int(row[2]))
            for row in self._session.execute(stmt).all()
        ]
