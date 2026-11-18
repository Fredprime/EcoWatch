"""Service layer for querying processing jobs and queue health summaries."""

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Principal
from ecowatch.modules.jobs.models import JobStatus
from ecowatch.modules.jobs.repository import JobsRepository
from ecowatch.modules.jobs.schemas import (
    JobSummaryResponse,
    JobTypeSummary,
    ProcessingJobResponse,
)


class JobsService:
    """System-admin service for inspecting background processing queues."""

    def __init__(self, session: Session) -> None:
        self._repo = JobsRepository(session)

    @staticmethod
    def _ensure_system_admin(principal: Principal) -> None:
        if not principal.is_system_admin:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only system_admin may inspect background processing jobs",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

    def get_summary(self, principal: Principal) -> JobSummaryResponse:
        """Return aggregate queue depths and failure counters per job type."""
        self._ensure_system_admin(principal)
        rows = self._repo.summarize_counts()
        byTypeMap: dict[str, JobTypeSummary] = {}
        totals = {s.value: 0 for s in JobStatus}

        for jobType, jobStatus, count in rows:
            entry = byTypeMap.setdefault(jobType, JobTypeSummary(jobType=jobType))
            if jobStatus in totals:
                totals[jobStatus] += count
                setattr(entry, jobStatus, getattr(entry, jobStatus) + count)

        return JobSummaryResponse(
            totalPending=totals[JobStatus.PENDING.value],
            totalProcessing=totals[JobStatus.PROCESSING.value],
            totalProcessed=totals[JobStatus.PROCESSED.value],
            totalFailed=totals[JobStatus.FAILED.value],
            totalDead=totals[JobStatus.DEAD.value],
            byType=sorted(byTypeMap.values(), key=lambda item: item.jobType),
        )

    def list_jobs(
        self,
        principal: Principal,
        *,
        statusFilter: JobStatus | None = None,
        jobType: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[ProcessingJobResponse]:
        """Return cursor-paginated processing jobs ordered newest first."""
        self._ensure_system_admin(principal)
        items, nextCursor, hasMore = self._repo.list_jobs(
            statusFilter=statusFilter,
            jobType=jobType,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[ProcessingJobResponse](
            items=[ProcessingJobResponse.model_validate(item) for item in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )
