"""SQLAlchemy repository for users, organisations, and memberships."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ecowatch.core.models import utc_now
from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.identity.models import Membership, Organisation, RevokedToken, User


class IdentityRepository:
    """Data-access operations for identity and tenant models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user_by_id(self, userId: uuid.UUID) -> User | None:
        return self._session.get(User, userId)

    def get_user_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        return self._session.scalar(select(User).where(User.email == normalized))

    def list_users(
        self,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[User], str | None, bool]:
        """Page through user accounts without exposing password hashes."""
        return paginate_descending(
            self._session,
            select(User),
            timeCol=User.createdAt,
            idCol=User.id,
            cursor=cursor,
            limit=limit,
        )

    def is_token_revoked(self, tokenId: uuid.UUID) -> bool:
        """Return True if a bearer token's jti has been explicitly revoked."""
        return self._session.get(RevokedToken, tokenId) is not None

    def revoke_token(
        self, tokenId: uuid.UUID, userId: uuid.UUID, expiresAt: datetime
    ) -> RevokedToken:
        """Idempotently record a token revocation."""
        existing = self._session.get(RevokedToken, tokenId)
        if existing is not None:
            return existing
        record = RevokedToken(tokenId=tokenId, userId=userId, expiresAt=expiresAt)
        self._session.add(record)
        self._session.flush()
        return record

    def purge_expired_revoked_tokens(
        self, now: datetime | None = None, *, limit: int = 500
    ) -> int:
        """Delete at most `limit` expired revoked_tokens rows and return the count."""
        cutoff = now or utc_now()
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        boundedLimit = max(1, min(limit, 500))
        expiredIds = (
            select(RevokedToken.tokenId)
            .where(RevokedToken.expiresAt < cutoff)
            .order_by(RevokedToken.expiresAt.asc(), RevokedToken.tokenId.asc())
            .limit(boundedLimit)
        )
        result = self._session.execute(
            delete(RevokedToken).where(RevokedToken.tokenId.in_(expiredIds))
        )
        return int(result.rowcount or 0)

    def create_user(
        self,
        *,
        email: str,
        displayName: str,
        passwordHash: str,
        systemRole: str | None = None,
        isActive: bool = True,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            displayName=displayName.strip(),
            passwordHash=passwordHash,
            systemRole=systemRole,
            isActive=isActive,
        )
        self._session.add(user)
        self._session.flush()
        return user

    def get_organisation_by_id(self, organisationId: uuid.UUID) -> Organisation | None:
        return self._session.get(Organisation, organisationId)

    def get_organisation_by_name(self, name: str) -> Organisation | None:
        return self._session.scalar(
            select(Organisation).where(Organisation.name == name.strip())
        )

    def create_organisation(
        self,
        *,
        name: str,
        orgType: str,
        isActive: bool = True,
    ) -> Organisation:
        organisation = Organisation(
            name=name.strip(),
            orgType=orgType.strip(),
            isActive=isActive,
        )
        self._session.add(organisation)
        self._session.flush()
        return organisation

    def list_organisations(
        self,
        *,
        organisationIds: set[uuid.UUID] | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Organisation], str | None, bool]:
        if organisationIds is not None and not organisationIds:
            return [], None, False

        stmt = select(Organisation)
        if organisationIds is not None:
            stmt = stmt.where(Organisation.id.in_(organisationIds))

        return paginate_descending(
            self._session,
            stmt,
            timeCol=Organisation.createdAt,
            idCol=Organisation.id,
            cursor=cursor,
            limit=limit,
        )

    def list_active_memberships_for_user(self, userId: uuid.UUID) -> list[Membership]:
        stmt = (
            select(Membership)
            .join(Organisation, Organisation.id == Membership.organisationId)
            .where(
                Membership.userId == userId,
                Membership.isActive.is_(True),
                Organisation.isActive.is_(True),
            )
            .order_by(Membership.createdAt.asc(), Membership.id.asc())
        )
        return list(self._session.scalars(stmt).all())

    def get_membership(
        self,
        *,
        userId: uuid.UUID,
        organisationId: uuid.UUID,
        role: str,
    ) -> Membership | None:
        return self._session.scalar(
            select(Membership).where(
                Membership.userId == userId,
                Membership.organisationId == organisationId,
                Membership.role == role,
            )
        )

    def upsert_membership(
        self,
        *,
        userId: uuid.UUID,
        organisationId: uuid.UUID,
        role: str,
        isActive: bool = True,
    ) -> Membership:
        membership = self.get_membership(
            userId=userId, organisationId=organisationId, role=role
        )
        if membership is None:
            membership = Membership(
                userId=userId,
                organisationId=organisationId,
                role=role,
                isActive=isActive,
            )
            self._session.add(membership)
        else:
            membership.isActive = isActive
        self._session.flush()
        return membership
