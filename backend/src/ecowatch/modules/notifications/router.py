"""FastAPI routes for clarification requests and user notification inbox."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import (
    get_current_principal,
    get_request_id,
    rate_limit_dependency,
    require_permission,
)
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.notifications.schemas import (
    ClarificationRequestResponse,
    CreateClarificationRequest,
    NotificationResponse,
)
from ecowatch.modules.notifications.service import NotificationService

router = APIRouter(tags=["notifications"])


@router.post(
    "/observations/{observationId}/clarifications",
    response_model=ClarificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            rate_limit_dependency(
                "messaging", "messagingRateLimit", "messagingWindowSeconds"
            )
        )
    ],
)
def create_clarification(
    payload: CreateClarificationRequest,
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.OBS_CLARIFY)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> ClarificationRequestResponse:
    """Send a clarification request to an observation's contributor (RV/IV/OA/SA)."""
    return NotificationService(db).request_clarification(
        principal,
        observationId,
        payload,
        requestId=requestId,
    )


@router.get("/notifications", response_model=CursorPage[NotificationResponse])
def list_notifications(
    unreadOnly: bool = Query(default=False),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CursorPage[NotificationResponse]:
    """List cursor-paginated notifications for the authenticated user's inbox."""
    return NotificationService(db).list_notifications(
        principal,
        unreadOnly=unreadOnly,
        cursor=cursor,
        limit=limit,
    )


@router.post("/notifications/{notificationId}/read", response_model=NotificationResponse)
def mark_notification_read(
    notificationId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification in the caller's own inbox as read."""
    return NotificationService(db).mark_read(principal, notificationId)
