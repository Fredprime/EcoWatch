"""FastAPI router for querying append-only audit events."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.audit.schemas import AuditEventResponse
from ecowatch.modules.audit.service import AuditService
from ecowatch.modules.identity.permissions import Permission, Principal

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=CursorPage[AuditEventResponse])
def list_audit_events(
    organisationId: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    targetType: str | None = Query(default=None),
    targetId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.AUDIT_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[AuditEventResponse]:
    """Return cursor-paginated audit events scoped by caller role and organisation."""
    return AuditService(db).list_events(
        principal,
        organisationId=organisationId,
        action=action,
        targetType=targetType,
        targetId=targetId,
        cursor=cursor,
        limit=limit,
    )
