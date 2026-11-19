"""FastAPI dependency providers for storage, authentication, RBAC, and request metadata."""

from collections.abc import Callable

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.rate_limit import check_and_increment_limit
from ecowatch.core.security import AuthProvider, LocalTokenAuthProvider
from ecowatch.core.storage import LocalFilesystemStorage, StorageProvider
from ecowatch.modules.identity.permissions import Permission, Principal, Role, SystemRole
from ecowatch.modules.identity.repository import IdentityRepository

_bearerScheme = HTTPBearer(auto_error=False)


def get_storage(settings: Settings = Depends(get_settings)) -> StorageProvider:
    """Provide the configured object storage backend."""
    return LocalFilesystemStorage(settings.storageRoot)


def get_auth_provider(settings: Settings = Depends(get_settings)) -> AuthProvider:
    """Provide the configured bearer token authentication provider."""
    return LocalTokenAuthProvider(settings.authSecret, settings.authTokenTtlSeconds)


def get_request_id(request: Request) -> str | None:
    """Return the active request ID assigned by middleware or incoming header."""
    requestId = getattr(request.state, "requestId", None)
    if isinstance(requestId, str) and requestId:
        return requestId
    return request.headers.get("X-Request-ID")


def get_optional_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearerScheme),
    db: Session = Depends(get_db),
    authProvider: AuthProvider = Depends(get_auth_provider),
) -> Principal:
    """Resolve an authenticated Principal from a bearer token, or return anonymous Principal."""
    if credentials is None:
        return Principal()

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Invalid authentication scheme",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )

    claims = authProvider.verify_token(credentials.credentials)
    if claims is None:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Invalid or expired authentication token",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )

    repo = IdentityRepository(db)
    if claims.tokenId is not None and repo.is_token_revoked(claims.tokenId):
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Authentication token has been revoked",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )

    user = repo.get_user_by_id(claims.userId)
    if user is None or not user.isActive:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Authenticated user is inactive or missing",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )

    systemRole = SystemRole(user.systemRole) if user.systemRole else None
    activeMemberships = tuple(
        (membership.organisationId, Role(membership.role))
        for membership in repo.list_active_memberships_for_user(user.id)
    )
    return Principal(
        userId=user.id,
        systemRole=systemRole,
        memberships=activeMemberships,
        isAuthenticated=True,
    )


def get_current_principal(
    principal: Principal = Depends(get_optional_principal),
) -> Principal:
    """Require an authenticated user principal, rejecting anonymous requests with 401."""
    if not principal.isAuthenticated or principal.userId is None:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Authentication required",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )
    return principal


def require_permission(permission: Permission) -> Callable[[Principal], Principal]:
    """Build a FastAPI dependency enforcing a server-side RBAC permission."""

    def _dependency(principal: Principal = Depends(get_optional_principal)) -> Principal:
        if principal.has_permission(permission):
            return principal
        if not principal.isAuthenticated:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        raise DomainError(
            ErrorCode.FORBIDDEN,
            f"Missing required permission: {permission.value}",
            statusCode=status.HTTP_403_FORBIDDEN,
        )

    return _dependency


def rate_limit_dependency(
    scope: str,
    maxAttemptsAttr: str,
    windowSecondsAttr: str,
) -> Callable[..., None]:
    """Build a FastAPI dependency enforcing DB-backed rate limits by user or client IP."""

    def _dependency(
        request: Request,
        principal: Principal = Depends(get_optional_principal),
        db: Session = Depends(get_db),
        settings: Settings = Depends(get_settings),
    ) -> None:
        actorKey = (
            f"user:{principal.userId}"
            if principal.isAuthenticated and principal.userId is not None
            else f"ip:{request.client.host if request.client else 'unknown'}"
        )
        bucketKey = f"rl:{scope}:{actorKey}"
        try:
            check_and_increment_limit(
                db,
                bucketKey,
                maxAttempts=getattr(settings, maxAttemptsAttr),
                windowSeconds=getattr(settings, windowSecondsAttr),
            )
            db.commit()
        except DomainError:
            db.commit()
            raise

    return _dependency
