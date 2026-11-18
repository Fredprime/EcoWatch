"""SQLAlchemy ORM models for clarification requests and user notifications."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class ClarificationRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Addressable clarification request sent to a contributor without exposing identity."""

    __tablename__ = "clarification_requests"

    observationId: Mapped[uuid.UUID] = mapped_column(
        "observation_id", Uuid(as_uuid=True), nullable=False, index=True
    )
    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id", Uuid(as_uuid=True), nullable=False, index=True
    )
    requestedByUserId: Mapped[uuid.UUID] = mapped_column(
        "requested_by_user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    recipientUserId: Mapped[uuid.UUID | None] = mapped_column(
        "recipient_user_id", Uuid(as_uuid=True), nullable=True, index=True
    )
    message: Mapped[str] = mapped_column("message", Text, nullable=False)
    deliveryChannel: Mapped[str] = mapped_column("delivery_channel", String(32), nullable=False)
    status: Mapped[str] = mapped_column("status", String(32), nullable=False, default="pending")
    responseText: Mapped[str | None] = mapped_column("response_text", Text, nullable=True)
    respondedAt: Mapped[datetime | None] = mapped_column(
        "responded_at", DateTime(timezone=True), nullable=True
    )


class Notification(Base, UUIDPrimaryKeyMixin):
    """In-app inbox notification delivered to an authenticated user."""

    __tablename__ = "notifications"

    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organisationId: Mapped[uuid.UUID | None] = mapped_column(
        "organisation_id", Uuid(as_uuid=True), nullable=True, index=True
    )
    notificationType: Mapped[str] = mapped_column(
        "notification_type", String(64), nullable=False
    )
    title: Mapped[str] = mapped_column("title", String(200), nullable=False)
    body: Mapped[str] = mapped_column("body", Text, nullable=False)
    targetType: Mapped[str | None] = mapped_column("target_type", String(64), nullable=True)
    targetId: Mapped[uuid.UUID | None] = mapped_column(
        "target_id", Uuid(as_uuid=True), nullable=True
    )
    isRead: Mapped[bool] = mapped_column("is_read", Boolean, nullable=False, default=False)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
