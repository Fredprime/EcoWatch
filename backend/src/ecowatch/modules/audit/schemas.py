"""Pydantic boundary schemas for audit events."""

import uuid
from datetime import datetime
from typing import Any

from ecowatch.core.schemas import CamelModel


class AuditEventResponse(CamelModel):
    """Public representation of an append-only audit event."""

    id: uuid.UUID
    occurredAt: datetime
    actorUserId: uuid.UUID | None = None
    actorRole: str
    organisationId: uuid.UUID | None = None
    action: str
    targetType: str
    targetId: uuid.UUID
    reason: str | None = None
    details: dict[str, Any]
    requestId: str | None = None
