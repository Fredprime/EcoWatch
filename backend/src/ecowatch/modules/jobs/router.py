"""FastAPI routes for inspecting processing job queues (SA only)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.jobs.models import JobStatus
from ecowatch.modules.jobs.schemas import JobSummaryResponse, ProcessingJobResponse
from ecowatch.modules.jobs.service import JobsService

router = APIRouter(tags=["jobs"])


@router.get("/jobs/summary", response_model=JobSummaryResponse)
def get_jobs_summary(
    principal: Principal = Depends(require_permission(Permission.JOBS_READ)),
    db: Session = Depends(get_db),
) -> JobSummaryResponse:
    """Return queue depth and failure counters per job type (system_admin only)."""
    return JobsService(db).get_summary(principal)


@router.get("/jobs", response_model=CursorPage[ProcessingJobResponse])
def list_jobs(
    statusFilter: JobStatus | None = Query(default=None, alias="status"),
    jobType: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.JOBS_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[ProcessingJobResponse]:
    """List cursor-paginated background processing jobs (system_admin only)."""
    return JobsService(db).list_jobs(
        principal,
        statusFilter=statusFilter,
        jobType=jobType,
        cursor=cursor,
        limit=limit,
    )
