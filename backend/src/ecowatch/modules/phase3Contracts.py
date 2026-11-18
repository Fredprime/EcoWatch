"""Shared Phase 3 boundary helpers for RBAC, tenant scope, validation, and audit."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.audit.service import AuditService
from ecowatch.modules.identity.permissions import Permission, Principal


def require_authenticated_user(principal: Principal) -> UUID:
    """Return the authenticated user id or reject the request."""
    if not principal.isAuthenticated or principal.userId is None:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Authentication is required",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )
    return principal.userId


def require_permission(
    principal: Principal,
    permission: Permission,
    organisationId: UUID,
) -> None:
    """Enforce deny-by-default RBAC scoped to an organisation without leaking tenancy."""
    if principal.is_system_admin:
        if principal.has_permission(permission):
            return
        raise DomainError(
            ErrorCode.FORBIDDEN,
            f"Missing permission: {permission.value}",
            statusCode=status.HTTP_403_FORBIDDEN,
        )
    if not principal.roles_for_org(organisationId):
        raise DomainError(
            ErrorCode.NOT_FOUND,
            "Resource not found.",
            statusCode=status.HTTP_404_NOT_FOUND,
            field="organisationId",
        )
    if not principal.has_permission(permission, organisationId):
        raise DomainError(
            ErrorCode.FORBIDDEN,
            f"Missing permission: {permission.value}",
            statusCode=status.HTTP_403_FORBIDDEN,
        )


def require_text(value: str | None, fieldName: str) -> None:
    """Reject missing or whitespace-only required text."""
    if value is None or not value.strip():
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"{fieldName} is required.",
            field=fieldName,
        )


def require_identifier(value: object | None, fieldName: str) -> None:
    """Reject a missing required identifier."""
    if value is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"{fieldName} is required.",
            field=fieldName,
        )


def record_event(
    session: Session,
    principal: Principal,
    *,
    organisationId: UUID,
    action: str,
    targetType: str,
    targetId: UUID,
    detail: dict[str, Any] | None = None,
    reason: str | None = None,
    requestId: str | None = None,
) -> None:
    """Append a Phase 3 audit event in the caller's transaction."""
    AuditService(session).record_event(
        actorUserId=principal.userId,
        actorRole=principal.primary_role_label,
        action=action,
        targetType=targetType,
        targetId=targetId,
        organisationId=organisationId,
        reason=reason,
        details=detail,
        requestId=requestId,
    )
