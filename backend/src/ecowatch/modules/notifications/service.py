"""Notifications and clarification request service layer."""

import uuid

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.identity.repository import IdentityRepository
from ecowatch.modules.notifications.repository import NotificationRepository
from ecowatch.modules.notifications.schemas import (
    ClarificationRequestResponse,
    CreateClarificationRequest,
    NotificationResponse,
)


class NotificationService:
    """Business logic for contributor clarifications and user notification inboxes."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = NotificationRepository(session)
        self._identityRepo = IdentityRepository(session)

    def _resolve_clarification_scope(
        self,
        observationId: uuid.UUID,
        requestedOrgId: uuid.UUID | None,
    ) -> tuple[uuid.UUID, uuid.UUID | None]:
        tableExists, obsOrgId, obsSubmitterId = self._repo.lookup_observation_scope(
            observationId
        )
        if not tableExists:
            if requestedOrgId is None:
                raise DomainError(
                    ErrorCode.VALIDATION_ERROR,
                    "organisationId is required",
                    statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    field="organisationId",
                )
            return requestedOrgId, None

        if obsOrgId is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if requestedOrgId is not None and requestedOrgId != obsOrgId:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "organisationId does not match the observation's organisation",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="organisationId",
            )
        return obsOrgId, obsSubmitterId

    def request_clarification(
        self,
        principal: Principal,
        observationId: uuid.UUID,
        payload: CreateClarificationRequest,
        *,
        requestId: str | None = None,
    ) -> ClarificationRequestResponse:
        """Create an observation clarification request with org-scoped RBAC and audit."""
        if principal.userId is None:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )

        resolvedOrgId, obsSubmitterId = self._resolve_clarification_scope(
            observationId, payload.organisationId
        )
        if not principal.has_permission(Permission.OBS_CLARIFY, resolvedOrgId):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Missing permission to request clarification for this organisation",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        recipientUserId = (
            payload.recipientUserId if payload.recipientUserId is not None else obsSubmitterId
        )
        if (
            recipientUserId is not None
            and self._identityRepo.get_user_by_id(recipientUserId) is None
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Recipient user not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        initialStatus = "sent" if recipientUserId is not None else "pending"
        clarification = self._repo.create_clarification(
            observationId=observationId,
            organisationId=resolvedOrgId,
            requestedByUserId=principal.userId,
            recipientUserId=recipientUserId,
            message=payload.message,
            deliveryChannel=payload.deliveryChannel.value,
            status=initialStatus,
        )

        if recipientUserId is not None:
            self._repo.create_notification(
                userId=recipientUserId,
                organisationId=resolvedOrgId,
                notificationType="clarification.requested",
                title="Clarification requested on your observation",
                body=clarification.message,
                targetType="observation",
                targetId=observationId,
            )

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=resolvedOrgId,
            action="clarification.requested",
            targetType="clarification_request",
            targetId=clarification.id,
            details={
                "observationId": str(observationId),
                "deliveryChannel": clarification.deliveryChannel,
                "hasRecipient": recipientUserId is not None,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(clarification)
        return ClarificationRequestResponse.model_validate(clarification)

    def list_notifications(
        self,
        principal: Principal,
        *,
        unreadOnly: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[NotificationResponse]:
        """List notifications belonging strictly to the authenticated caller."""
        if principal.userId is None:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        items, nextCursor, hasMore = self._repo.list_notifications_for_user(
            userId=principal.userId,
            unreadOnly=unreadOnly,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[NotificationResponse](
            items=[NotificationResponse.model_validate(item) for item in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def mark_read(
        self,
        principal: Principal,
        notificationId: uuid.UUID,
    ) -> NotificationResponse:
        """Mark a notification in the caller's own inbox as read."""
        if principal.userId is None:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        notification = self._repo.get_notification(notificationId)
        if notification is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Notification not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if notification.userId != principal.userId:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Cannot modify another user's notification",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if not notification.isRead:
            notification.isRead = True
            self._session.commit()
            self._session.refresh(notification)
        return NotificationResponse.model_validate(notification)
