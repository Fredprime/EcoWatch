"""Pydantic boundary schemas for clarification requests and user notifications."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import Field

from ecowatch.core.schemas import CamelModel


class DeliveryChannel(StrEnum):
    """Supported delivery channels for contributor clarification requests."""

    IN_APP = "in_app"
    RECEIPT_PORTAL = "receipt_portal"
    EMAIL = "email"


class CreateClarificationRequest(CamelModel):
    """Staff request to ask a contributor for clarification on an observation."""

    organisationId: uuid.UUID | None = None
    recipientUserId: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=2000)
    deliveryChannel: DeliveryChannel = DeliveryChannel.IN_APP


class ClarificationRequestResponse(CamelModel):
    """Public representation of a clarification request."""

    id: uuid.UUID
    observationId: uuid.UUID
    organisationId: uuid.UUID
    requestedByUserId: uuid.UUID
    recipientUserId: uuid.UUID | None = None
    message: str
    deliveryChannel: str
    status: str
    responseText: str | None = None
    respondedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class NotificationResponse(CamelModel):
    """Public representation of an in-app notification."""

    id: uuid.UUID
    userId: uuid.UUID
    organisationId: uuid.UUID | None = None
    notificationType: str
    title: str
    body: str
    targetType: str | None = None
    targetId: uuid.UUID | None = None
    isRead: bool
    createdAt: datetime
