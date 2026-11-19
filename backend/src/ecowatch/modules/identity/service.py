"""Identity service handling authentication, users, organisations, and memberships."""

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings, get_settings
from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.rate_limit import check_and_increment_limit, reset_limit
from ecowatch.core.schemas import CursorPage
from ecowatch.core.security import AuthProvider, hash_password, verify_password
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.identity.permissions import Principal, Role, SystemRole
from ecowatch.modules.identity.repository import IdentityRepository
from ecowatch.modules.identity.schemas import (
    AssignMembershipRequest,
    AuthMeResponse,
    CreateOrganisationRequest,
    CreateUserRequest,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MembershipResponse,
    OrganisationResponse,
    UserResponse,
)


def login_bucket_key(email: str, clientIp: str) -> str:
    """Build a stable login throttle key without storing the email or IP in plaintext."""
    fingerprint = f"{email.strip().lower()}|{clientIp}".encode()
    return f"login:{hashlib.sha256(fingerprint).hexdigest()}"


class IdentityService:
    """Application service for local auth, tenant organisations, and RBAC memberships."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._repo = IdentityRepository(session)

    def login(
        self,
        payload: LoginRequest,
        authProvider: AuthProvider,
        *,
        clientIp: str = "unknown",
    ) -> LoginResponse:
        """Authenticate credentials and issue a token, throttling repeated failures."""
        bucketKey = login_bucket_key(payload.email, clientIp)
        settings = self._settings
        try:
            check_and_increment_limit(
                self._session,
                bucketKey,
                maxAttempts=settings.loginMaxAttempts,
                windowSeconds=settings.loginWindowSeconds,
                lockoutSeconds=settings.loginLockoutSeconds,
            )
        except DomainError:
            self._session.commit()
            raise

        user = self._repo.get_user_by_email(payload.email)
        if (
            user is None
            or not user.isActive
            or not verify_password(payload.password, user.passwordHash)
        ):
            self._session.commit()
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Invalid email or password",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )

        reset_limit(self._session, bucketKey)
        token = authProvider.issue_token(user.id)
        self._session.commit()
        return LoginResponse(
            accessToken=token,
            user=UserResponse.model_validate(user),
        )

    def logout(
        self,
        principal: Principal,
        token: str,
        authProvider: AuthProvider,
        *,
        requestId: str | None = None,
    ) -> LogoutResponse:
        """Revoke the caller's current bearer token server-side and audit the logout."""
        claims = authProvider.verify_token(token)
        if claims is None or claims.tokenId is None or principal.userId != claims.userId:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Invalid or missing authentication token",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        expiresAt = datetime.fromtimestamp(claims.expiresAt, tz=UTC)
        self._repo.revoke_token(claims.tokenId, claims.userId, expiresAt)
        self._repo.purge_expired_revoked_tokens()
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=None,
            action="auth.logout",
            targetType="user",
            targetId=claims.userId,
            requestId=requestId,
        )
        self._session.commit()
        return LogoutResponse(revoked=True)

    def get_me(self, principal: Principal) -> AuthMeResponse:
        """Return the authenticated user's profile and active organisation memberships."""
        if principal.userId is None:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        user = self._repo.get_user_by_id(principal.userId)
        if user is None or not user.isActive:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user is inactive or missing",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        memberships = self._repo.list_active_memberships_for_user(user.id)
        userData = UserResponse.model_validate(user).model_dump()
        return AuthMeResponse(
            **userData,
            memberships=[MembershipResponse.model_validate(item) for item in memberships],
        )

    def create_user(
        self,
        principal: Principal,
        payload: CreateUserRequest,
        *,
        requestId: str | None = None,
    ) -> UserResponse:
        """Create a user account (system_admin only) with atomic audit event."""
        if not principal.is_system_admin:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only system_admin may create users",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if self._repo.get_user_by_email(payload.email) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A user with this email already exists",
                statusCode=status.HTTP_409_CONFLICT,
                field="email",
            )
        user = self._repo.create_user(
            email=payload.email,
            displayName=payload.displayName,
            passwordHash=hash_password(payload.password),
            systemRole=payload.systemRole.value if payload.systemRole else None,
            isActive=payload.isActive,
        )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action="user.created",
            targetType="user",
            targetId=user.id,
            details={
                "systemRole": user.systemRole,
                "isActive": user.isActive,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(user)
        return UserResponse.model_validate(user)

    def create_organisation(
        self,
        principal: Principal,
        payload: CreateOrganisationRequest,
        *,
        requestId: str | None = None,
    ) -> OrganisationResponse:
        """Create a tenant organisation (system_admin only) with atomic audit event."""
        if not principal.is_system_admin:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only system_admin may create organisations",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if self._repo.get_organisation_by_name(payload.name) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "An organisation with this name already exists",
                statusCode=status.HTTP_409_CONFLICT,
                field="name",
            )
        org = self._repo.create_organisation(
            name=payload.name,
            orgType=payload.orgType,
            isActive=payload.isActive,
        )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=org.id,
            action="organisation.created",
            targetType="organisation",
            targetId=org.id,
            details={"orgType": org.orgType, "isActive": org.isActive},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(org)
        return OrganisationResponse.model_validate(org)

    def list_organisations(
        self,
        principal: Principal,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[OrganisationResponse]:
        """List organisations visible to the authenticated principal."""
        allowedIds: set[uuid.UUID] | None = None
        if not principal.is_system_admin:
            allowedIds = {orgId for orgId, _ in principal.memberships}
        items, nextCursor, hasMore = self._repo.list_organisations(
            organisationIds=allowedIds,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[OrganisationResponse](
            items=[OrganisationResponse.model_validate(org) for org in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def assign_membership(
        self,
        principal: Principal,
        organisationId: uuid.UUID,
        payload: AssignMembershipRequest,
        *,
        requestId: str | None = None,
    ) -> MembershipResponse:
        """Assign or update a membership (SA globally, OA for own org) and audit role.changed."""
        isOrgAdmin = Role.ORGANISATION_ADMIN in principal.roles_for_org(organisationId)
        if not principal.is_system_admin and not isOrgAdmin:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Cannot manage memberships for another organisation",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        if payload.role == Role.ANONYMOUS_CONTRIBUTOR:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "anonymous_contributor cannot be assigned as an organisation membership",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="role",
            )

        if payload.role == Role.SYSTEM_ADMIN:
            if not principal.is_system_admin:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Only system_admin may grant system_admin",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            if payload.userId == principal.userId:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "system_admin cannot be self-granted",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )

        org = self._repo.get_organisation_by_id(organisationId)
        if org is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Organisation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        targetUser = self._repo.get_user_by_id(payload.userId)
        if targetUser is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "User not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        if payload.role == Role.SYSTEM_ADMIN:
            targetUser.systemRole = SystemRole.SYSTEM_ADMIN.value if payload.isActive else None

        membership = self._repo.upsert_membership(
            userId=targetUser.id,
            organisationId=org.id,
            role=payload.role.value,
            isActive=payload.isActive,
        )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=org.id,
            action="role.changed",
            targetType="membership",
            targetId=membership.id,
            reason=payload.reason,
            details={
                "targetUserId": str(targetUser.id),
                "role": payload.role.value,
                "isActive": payload.isActive,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(membership)
        return MembershipResponse.model_validate(membership)
