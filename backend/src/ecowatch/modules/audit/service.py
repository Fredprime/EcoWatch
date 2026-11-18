"""Audit trail service and atomic transactional recording helper."""

import uuid
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.audit.repository import AuditRepository
from ecowatch.modules.audit.schemas import AuditEventResponse
from ecowatch.modules.identity.permissions import Permission, Principal


def record_audit_event(
    session: Session,
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
    """Write an audit event in the caller's session without committing."""
    return AuditRepository(session).create(
        actorUserId=actorUserId,
        actorRole=actorRole,
        action=action,
        targetType=targetType,
        targetId=targetId,
        organisationId=organisationId,
        reason=reason,
        details=details,
        requestId=requestId,
    )


class AuditService:
    """Service layer for recording and querying organisation-scoped audit events."""

    def __init__(self, session: Session) -> None:
        self._repo = AuditRepository(session)

    def record_event(
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
        """Record an audit event in the active transaction without committing."""
        return self._repo.create(
            actorUserId=actorUserId,
            actorRole=actorRole,
            action=action,
            targetType=targetType,
            targetId=targetId,
            organisationId=organisationId,
            reason=reason,
            details=details,
            requestId=requestId,
        )

    def list_events(
        self,
        principal: Principal,
        *,
        organisationId: uuid.UUID | None = None,
        action: str | None = None,
        targetType: str | None = None,
        targetId: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[AuditEventResponse]:
        """List audit events: SA sees all, OA sees own organisation(s) only."""
        allowedOrgIds: set[uuid.UUID] | None = None
        if not principal.is_system_admin:
            allowedOrgIds = principal.accessible_org_ids(Permission.AUDIT_READ)
            if not allowedOrgIds:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Missing permission to read audit events",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            if organisationId is not None and organisationId not in allowedOrgIds:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Cannot read audit events for another organisation",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )

        items, nextCursor, hasMore = self._repo.list_events(
            organisationIds=allowedOrgIds,
            organisationId=organisationId,
            action=action,
            targetType=targetType,
            targetId=targetId,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[AuditEventResponse](
            items=[AuditEventResponse.model_validate(item) for item in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )
