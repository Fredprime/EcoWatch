"""Shared read helpers for Phase 3 list endpoints (ADR-037).

Read gates reuse each module's existing WRITE permission because the permission
matrix has no dedicated ``*_READ`` value for these modules. The route dependency
checks the permission globally; these helpers enforce organisation scoping on
every query so a new list path cannot leak across tenants.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy import Select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.identity.permissions import Permission, Principal


def read_scope(principal: Principal, permission: Permission) -> set[UUID] | None:
    """Return the organisations a principal may read, or None for a system admin.

    A system admin holds the permission platform-wide and sees every organisation.
    Any other principal with no granting membership gets 403 rather than an
    always-empty page, so a misconfiguration is visible.
    """
    if principal.is_system_admin:
        return None
    allowedOrgIds = principal.accessible_org_ids(permission)
    if not allowedOrgIds:
        raise DomainError(
            ErrorCode.FORBIDDEN,
            f"Missing permission to read: {permission.value}",
            statusCode=status.HTTP_403_FORBIDDEN,
        )
    return allowedOrgIds


def scope_statement(
    stmt: Select[Any],
    model: Any,
    allowedOrgIds: set[UUID] | None,
    organisationId: UUID | None = None,
) -> Select[Any]:
    """Apply organisation scoping and an optional explicit organisation filter."""
    if allowedOrgIds is not None:
        if organisationId is not None and organisationId not in allowedOrgIds:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Cannot read records for another organisation",
                statusCode=status.HTTP_403_FORBIDDEN,
                field="organisationId",
            )
        stmt = stmt.where(model.organisationId.in_(allowedOrgIds))
    if organisationId is not None:
        stmt = stmt.where(model.organisationId == organisationId)
    return stmt


def list_page(
    session: Session,
    stmt: Select[Any],
    model: Any,
    *,
    cursor: str | None,
    limit: int,
) -> tuple[list[Any], str | None, bool]:
    """Apply descending (createdAt, id) keyset pagination to a scoped select."""
    return paginate_descending(
        session,
        stmt,
        timeCol=model.createdAt,
        idCol=model.id,
        cursor=cursor,
        limit=limit,
    )


def load_scoped_parent(
    session: Session,
    model: Any,
    parentId: UUID,
    allowedOrgIds: set[UUID] | None,
    *,
    fieldName: str,
    label: str,
) -> Any:
    """Load a parent record within the read scope, hiding cross-org parents as 404."""
    record = session.get(model, parentId)
    if record is None or (
        allowedOrgIds is not None and record.organisationId not in allowedOrgIds
    ):
        raise DomainError(
            ErrorCode.NOT_FOUND,
            f"{label} not found.",
            statusCode=status.HTTP_404_NOT_FOUND,
            field=fieldName,
        )
    return record
