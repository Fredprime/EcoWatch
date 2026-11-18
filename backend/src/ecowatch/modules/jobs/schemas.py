"""Pydantic schemas for processing jobs and queue summary metrics."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.jobs.models import JobStatus


class ProcessingJobResponse(CamelModel):
    """Serialized processing job record."""

    id: uuid.UUID
    jobType: str
    payload: dict[str, Any]
    status: JobStatus
    attempts: int
    maxAttempts: int
    availableAt: datetime
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    lastError: str | None = None
    createdAt: datetime
    updatedAt: datetime


class JobTypeSummary(CamelModel):
    """Queue depth and failure counters for a single job type."""

    jobType: str
    pending: int = 0
    processing: int = 0
    processed: int = 0
    failed: int = 0
    dead: int = 0


class JobSummaryResponse(CamelModel):
    """Platform-wide job queue depth and failure counters."""

    totalPending: int = 0
    totalProcessing: int = 0
    totalProcessed: int = 0
    totalFailed: int = 0
    totalDead: int = 0
    byType: list[JobTypeSummary] = Field(default_factory=list)
