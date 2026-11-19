"""Database-backed rate limiting, burst abuse logging, and tracking-code attempt lockout."""

import logging
import math
from datetime import UTC, datetime, timedelta

from fastapi import status
from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import Base, utc_now

_logger = logging.getLogger("ecowatch")


class RateLimitBucket(Base):
    """Persistent rate-limit counter surviving application restarts."""

    __tablename__ = "rate_limit_buckets"

    bucketKey: Mapped[str] = mapped_column("bucket_key", String(255), primary_key=True)
    windowStartedAt: Mapped[datetime] = mapped_column(
        "window_started_at", DateTime(timezone=True), nullable=False
    )
    attemptCount: Mapped[int] = mapped_column("attempt_count", Integer, nullable=False, default=0)
    lockedUntil: Mapped[datetime | None] = mapped_column(
        "locked_until", DateTime(timezone=True), nullable=True
    )


def check_and_increment_limit(
    session: Session,
    bucketKey: str,
    *,
    maxAttempts: int,
    windowSeconds: int,
    lockoutSeconds: int | None = None,
    lockoutCode: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
    now: datetime | None = None,
) -> None:
    """Enforce a fixed-window rate limit (and optional lockout) backed by the database."""
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)

    bucket = session.execute(
        select(RateLimitBucket).where(RateLimitBucket.bucketKey == bucketKey)
    ).scalar_one_or_none()

    if bucket is None:
        bucket = RateLimitBucket(
            bucketKey=bucketKey,
            windowStartedAt=current,
            attemptCount=1,
            lockedUntil=None,
        )
        session.add(bucket)
        session.flush()
        return

    if bucket.lockedUntil is not None:
        lockedUntil = (
            bucket.lockedUntil.replace(tzinfo=UTC)
            if bucket.lockedUntil.tzinfo is None
            else bucket.lockedUntil
        )
        if lockedUntil > current:
            retryAfter = max(1, math.ceil((lockedUntil - current).total_seconds()))
            _logger.warning(
                "abuse_burst_detected",
                extra={
                    "structured": {
                        "statusCode": status.HTTP_429_TOO_MANY_REQUESTS,
                        "errorCode": lockoutCode.value,
                    }
                },
            )
            raise DomainError(
                lockoutCode,
                "Too many attempts; please wait before retrying",
                statusCode=status.HTTP_429_TOO_MANY_REQUESTS,
                retryAfterSeconds=retryAfter,
            )
        bucket.lockedUntil = None
        bucket.windowStartedAt = current
        bucket.attemptCount = 0

    windowStart = (
        bucket.windowStartedAt.replace(tzinfo=UTC)
        if bucket.windowStartedAt.tzinfo is None
        else bucket.windowStartedAt
    )
    if (current - windowStart).total_seconds() >= windowSeconds:
        bucket.windowStartedAt = current
        bucket.attemptCount = 1
        session.flush()
        return

    bucket.attemptCount += 1
    if bucket.attemptCount > maxAttempts:
        retryAfter = lockoutSeconds
        if lockoutSeconds is not None:
            bucket.lockedUntil = current + timedelta(seconds=lockoutSeconds)
        else:
            retryAfter = max(1, math.ceil(windowSeconds - (current - windowStart).total_seconds()))
        session.flush()
        _logger.warning(
            "rate_limit_exceeded",
            extra={
                "structured": {
                    "statusCode": status.HTTP_429_TOO_MANY_REQUESTS,
                    "errorCode": lockoutCode.value,
                }
            },
        )
        raise DomainError(
            lockoutCode,
            "Rate limit exceeded; please retry later",
            statusCode=status.HTTP_429_TOO_MANY_REQUESTS,
            retryAfterSeconds=max(1, int(retryAfter)),
        )
    session.flush()


def reset_limit(session: Session, bucketKey: str) -> None:
    """Clear a rate-limit bucket (e.g., on successful tracking-code verification)."""
    bucket = session.execute(
        select(RateLimitBucket).where(RateLimitBucket.bucketKey == bucketKey)
    ).scalar_one_or_none()
    if bucket is not None:
        session.delete(bucket)
        session.flush()
