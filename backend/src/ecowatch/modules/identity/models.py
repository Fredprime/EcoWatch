"""SQLAlchemy ORM models for users, organisations, and role memberships."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered platform user account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        "email", String(255), unique=True, nullable=False, index=True
    )
    displayName: Mapped[str] = mapped_column("display_name", String(120), nullable=False)
    passwordHash: Mapped[str] = mapped_column("password_hash", String(255), nullable=False)
    systemRole: Mapped[str | None] = mapped_column("system_role", String(64), nullable=True)
    isActive: Mapped[bool] = mapped_column("is_active", Boolean, nullable=False, default=True)


class Organisation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tenant organisation scoping cases, observations, and memberships."""

    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column("name", String(200), unique=True, nullable=False)
    orgType: Mapped[str] = mapped_column("org_type", String(64), nullable=False)
    isActive: Mapped[bool] = mapped_column("is_active", Boolean, nullable=False, default=True)


class Membership(Base, UUIDPrimaryKeyMixin):
    """Organisation-scoped role assignment for a user."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organisation_id", "role", name="uq_memberships_user_org_role"),
    )

    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organisationId: Mapped[uuid.UUID] = mapped_column(
        "organisation_id",
        Uuid(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column("role", String(64), nullable=False)
    isActive: Mapped[bool] = mapped_column("is_active", Boolean, nullable=False, default=True)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utc_now
    )
