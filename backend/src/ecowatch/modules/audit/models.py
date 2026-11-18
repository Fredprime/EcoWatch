"""SQLAlchemy ORM model for append-only audit events."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, UUIDPrimaryKeyMixin, utc_now


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    """Append-only record of consequential platform actions without PII or secrets."""

    __tablename__ = "audit_events"

    occurredAt: Mapped[datetime] = mapped_column(
        "occurred_at", DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    actorUserId: Mapped[uuid.UUID | None] = mapped_column(
        "actor_user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    actorRole: Mapped[str] = mapped_column("actor_role", String(64), nullable=False)
    organisationId: Mapped[uuid.UUID | None] = mapped_column(
        "organisation_id", Uuid(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column("action", String(100), nullable=False, index=True)
    targetType: Mapped[str] = mapped_column("target_type", String(64), nullable=False)
    targetId: Mapped[uuid.UUID] = mapped_column("target_id", Uuid(as_uuid=True), nullable=False)
    reason: Mapped[str | None] = mapped_column("reason", Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column("details", JSON, nullable=False, default=dict)
    requestId: Mapped[str | None] = mapped_column("request_id", String(100), nullable=True)
