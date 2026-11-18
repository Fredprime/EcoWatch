"""SQLAlchemy ORM model and status enum for database-backed processing jobs."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class JobStatus(StrEnum):
    """Lifecycle states of an asynchronous processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD = "dead"


class ProcessingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Transactional database queue entry claimed with FOR UPDATE SKIP LOCKED."""

    __tablename__ = "processing_jobs"

    jobType: Mapped[str] = mapped_column("job_type", String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        "payload", JSON, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        "status", String(32), nullable=False, default=JobStatus.PENDING.value, index=True
    )
    attempts: Mapped[int] = mapped_column("attempts", Integer, nullable=False, default=0)
    maxAttempts: Mapped[int] = mapped_column("max_attempts", Integer, nullable=False, default=5)
    availableAt: Mapped[datetime] = mapped_column(
        "available_at", DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    startedAt: Mapped[datetime | None] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completedAt: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    lastError: Mapped[str | None] = mapped_column("last_error", Text, nullable=True)
