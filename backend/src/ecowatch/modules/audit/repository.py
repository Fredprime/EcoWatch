"""Append-only repository for audit_events (create and list only)."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.audit.models import AuditEvent


class AuditRepository:
    """Repository supporting only creation and keyset-paginated queries for audit events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        actorUserId: uuid.UUID | None,
        actorRole: str,
        action: str,
        targetType: str,
        targetId: uuid.UUID,
        organisationId: uuid.UUID | None = None,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
        requestId: str | None = None,
    ) -> AuditEvent:
        """Persist a new audit event within the caller's active transaction."""
        event = AuditEvent(
            actorUserId=actorUserId,
            actorRole=actorRole,
            organisationId=organisationId,
            action=action,
            targetType=targetType,
            targetId=targetId,
            reason=reason,
            details=dict(details) if details is not None else {},
            requestId=requestId,
        )
        self._session.add(event)
        self._session.flush()
        return event

    def list_events(
        self,
        *,
        organisationIds: set[uuid.UUID] | None = None,
        organisationId: uuid.UUID | None = None,
        action: str | None = None,
        targetType: str | None = None,
        targetId: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], str | None, bool]:
        """Return a cursor-paginated slice of audit events ordered newest first."""
        if organisationIds is not None and not organisationIds:
            return [], None, False

        stmt = select(AuditEvent)
        if organisationIds is not None:
            stmt = stmt.where(AuditEvent.organisationId.in_(organisationIds))
        if organisationId is not None:
            stmt = stmt.where(AuditEvent.organisationId == organisationId)
        if action is not None:
            stmt = stmt.where(AuditEvent.action == action)
        if targetType is not None:
            stmt = stmt.where(AuditEvent.targetType == targetType)
        if targetId is not None:
            stmt = stmt.where(AuditEvent.targetId == targetId)

        return paginate_descending(
            self._session,
            stmt,
            timeCol=AuditEvent.occurredAt,
            idCol=AuditEvent.id,
            cursor=cursor,
            limit=limit,
        )
