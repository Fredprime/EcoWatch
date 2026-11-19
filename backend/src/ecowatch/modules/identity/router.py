"""FastAPI routes for authentication, users, organisations, and memberships."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import (
    get_auth_provider,
    get_current_principal,
    get_request_id,
    require_permission,
)
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.core.security import AuthProvider
from ecowatch.modules.identity.permissions import Permission, Principal
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
from ecowatch.modules.identity.service import IdentityService

router = APIRouter(tags=["identity"])
_bearerScheme = HTTPBearer(auto_error=False)


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    authProvider: AuthProvider = Depends(get_auth_provider),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Authenticate with email and password to receive a bearer token."""
    clientIp = request.client.host if request.client else "unknown"
    return IdentityService(db, settings).login(payload, authProvider, clientIp=clientIp)


@router.post("/auth/logout", response_model=LogoutResponse)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearerScheme),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    authProvider: AuthProvider = Depends(get_auth_provider),
    requestId: str | None = Depends(get_request_id),
) -> LogoutResponse:
    """Revoke the caller's active bearer token server-side."""
    token = credentials.credentials if credentials is not None else ""
    return IdentityService(db).logout(
        principal, token, authProvider, requestId=requestId
    )


@router.get("/auth/me", response_model=AuthMeResponse)
def get_me(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    """Return the currently authenticated user profile and active memberships."""
    return IdentityService(db).get_me(principal)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> UserResponse:
    """Create a user account (system_admin only)."""
    return IdentityService(db).create_user(principal, payload, requestId=requestId)


@router.post(
    "/organisations",
    response_model=OrganisationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organisation(
    payload: CreateOrganisationRequest,
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> OrganisationResponse:
    """Create a tenant organisation (system_admin only)."""
    return IdentityService(db).create_organisation(principal, payload, requestId=requestId)


@router.get("/organisations", response_model=CursorPage[OrganisationResponse])
def list_organisations(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CursorPage[OrganisationResponse]:
    """List organisations accessible to the authenticated principal."""
    return IdentityService(db).list_organisations(principal, cursor=cursor, limit=limit)


@router.post(
    "/organisations/{orgId}/memberships",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_membership(
    payload: AssignMembershipRequest,
    orgId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.ORG_MANAGE_USERS)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> MembershipResponse:
    """Assign or update a user's organisation role (SA or OA for own org)."""
    return IdentityService(db).assign_membership(
        principal,
        orgId,
        payload,
        requestId=requestId,
    )
