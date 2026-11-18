"""SQLAlchemy repository for clarification requests and user notifications."""

import uuid

from sqlalchemy import Uuid, column, inspect, select, table
from sqlalchemy.orm import Session

from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.notifications.models import ClarificationRequest, Notification


class NotificationRepository:
    """Data-access operations for clarification requests and notifications."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def lookup_observation_scope(
        self, observationId: uuid.UUID
    ) -> tuple[bool, uuid.UUID | None, uuid.UUID | None]:
        """Return (tableExists, organisationId, submittedByUserId) without ORM coupling."""
        bind = self._session.get_bind()
        if bind is None or not inspect(bind).has_table("observations"):
            return False, None, None

        obsTable = table(
            "observations",
            column("id", Uuid(as_uuid=True)),
            column("organisation_id", Uuid(as_uuid=True)),
            column("submitted_by_user_id", Uuid(as_uuid=True)),
        )
        row = self._session.execute(
            select(obsTable.c.organisation_id, obsTable.c.submitted_by_user_id).where(
                obsTable.c.id == observationId
            )
        ).one_or_none()
        if row is None:
            return True, None, None
        return True, row[0], row[1]

    def create_clarification(
        self,
        *,
        observationId: uuid.UUID,
        organisationId: uuid.UUID,
        requestedByUserId: uuid.UUID,
        recipientUserId: uuid.UUID | None,
        message: str,
        deliveryChannel: str,
        status: str,
    ) -> ClarificationRequest:
        clarification = ClarificationRequest(
            observationId=observationId,
            organisationId=organisationId,
            requestedByUserId=requestedByUserId,
            recipientUserId=recipientUserId,
            message=message.strip(),
            deliveryChannel=deliveryChannel,
            status=status,
        )
        self._session.add(clarification)
        self._session.flush()
        return clarification

    def create_notification(
        self,
        *,
        userId: uuid.UUID,
        organisationId: uuid.UUID | None,
        notificationType: str,
        title: str,
        body: str,
        targetType: str | None = None,
        targetId: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            userId=userId,
            organisationId=organisationId,
            notificationType=notificationType,
            title=title,
            body=body,
            targetType=targetType,
            targetId=targetId,
        )
        self._session.add(notification)
        self._session.flush()
        return notification

    def get_notification(self, notificationId: uuid.UUID) -> Notification | None:
        return self._session.get(Notification, notificationId)

    def list_notifications_for_user(
        self,
        *,
        userId: uuid.UUID,
        unreadOnly: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Notification], str | None, bool]:
        stmt = select(Notification).where(Notification.userId == userId)
        if unreadOnly:
            stmt = stmt.where(Notification.isRead.is_(False))
        return paginate_descending(
            self._session,
            stmt,
            timeCol=Notification.createdAt,
            idCol=Notification.id,
            cursor=cursor,
            limit=limit,
        )
