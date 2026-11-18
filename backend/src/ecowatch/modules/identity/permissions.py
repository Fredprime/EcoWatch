"""Deny-by-default RBAC roles, Phase 1 permissions, and Principal authority helpers."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from fastapi import status

from ecowatch.core.errors import DomainError, ErrorCode


class Role(StrEnum):
    """Canonical EcoWatch roles from docs/PERMISSIONS_MATRIX.md."""

    ANONYMOUS_CONTRIBUTOR = "anonymous_contributor"
    REGISTERED_CONTRIBUTOR = "registered_contributor"
    REVIEWER = "reviewer"
    INVESTIGATOR = "investigator"
    ENVIRONMENTAL_SPECIALIST = "environmental_specialist"
    INTERVENTION_MANAGER = "intervention_manager"
    ORGANISATION_ADMIN = "organisation_admin"
    SYSTEM_ADMIN = "system_admin"


class SystemRole(StrEnum):
    """Platform-wide system roles stored on User.systemRole."""

    SYSTEM_ADMIN = "system_admin"


class Permission(StrEnum):
    """Fine-grained Phase 1 resource permissions."""

    OBS_CREATE = "obs:create"
    OBS_READ_OWN = "obs:read_own"
    OBS_READ_REDACTED = "obs:read_redacted"
    OBS_READ_RESTRICTED = "obs:read_restricted"
    OBS_CORRECT = "obs:correct"
    OBS_QUALITY_FLAG = "obs:quality_flag"
    OBS_CLARIFY = "obs:clarify"
    OBS_HIDE = "obs:hide"
    SOURCE_READ = "source:read"
    EVIDENCE_UPLOAD = "evidence:upload"
    EVIDENCE_READ_DERIVATIVE = "evidence:read_derivative"
    EVIDENCE_READ_ORIGINAL = "evidence:read_original"
    EVIDENCE_READ_SCAN_STATUS = "evidence:read_scan_status"
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_UPDATE = "case:update"
    CASE_ASSIGN = "case:assign"
    CASE_LINK_OBS = "case:link_obs"
    CASE_TRANSITION_BASIC = "case:transition_basic"
    CASE_TRANSITION_FIELD_VERIFIED = "case:transition_field_verified"
    CASE_TRANSITION_REFER = "case:transition_refer"
    CASE_TRANSITION_CLOSE = "case:transition_close"
    CORRELATION_READ = "correlation:read"
    CORRELATION_REVIEW = "correlation:review"
    AUDIT_READ = "audit:read"
    ORG_MANAGE_USERS = "org:manage_users"
    ADMIN_MANAGE_SYSTEM = "admin:manage_system"
    JOBS_READ = "jobs:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ANONYMOUS_CONTRIBUTOR: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_OWN,
            Permission.EVIDENCE_UPLOAD,
        }
    ),
    Role.REGISTERED_CONTRIBUTOR: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_OWN,
            Permission.OBS_CORRECT,
            Permission.EVIDENCE_UPLOAD,
        }
    ),
    Role.REVIEWER: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.OBS_CORRECT,
            Permission.OBS_QUALITY_FLAG,
            Permission.OBS_CLARIFY,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.EVIDENCE_READ_SCAN_STATUS,
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_LINK_OBS,
            Permission.CASE_TRANSITION_BASIC,
            Permission.CORRELATION_READ,
            Permission.CORRELATION_REVIEW,
        }
    ),
    Role.INVESTIGATOR: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.OBS_READ_RESTRICTED,
            Permission.OBS_CORRECT,
            Permission.OBS_CLARIFY,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.EVIDENCE_READ_ORIGINAL,
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_LINK_OBS,
            Permission.CASE_TRANSITION_BASIC,
            Permission.CASE_TRANSITION_REFER,
            Permission.CASE_TRANSITION_CLOSE,
            Permission.CORRELATION_READ,
            Permission.CORRELATION_REVIEW,
        }
    ),
    Role.ENVIRONMENTAL_SPECIALIST: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.OBS_READ_RESTRICTED,
            Permission.OBS_QUALITY_FLAG,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.EVIDENCE_READ_ORIGINAL,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_TRANSITION_FIELD_VERIFIED,
            Permission.CORRELATION_READ,
            Permission.CORRELATION_REVIEW,
        }
    ),
    Role.INTERVENTION_MANAGER: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.CASE_READ,
        }
    ),
    Role.ORGANISATION_ADMIN: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.OBS_READ_RESTRICTED,
            Permission.OBS_CLARIFY,
            Permission.SOURCE_READ,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.EVIDENCE_READ_ORIGINAL,
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_ASSIGN,
            Permission.CASE_TRANSITION_BASIC,
            Permission.CASE_TRANSITION_FIELD_VERIFIED,
            Permission.CASE_TRANSITION_REFER,
            Permission.CASE_TRANSITION_CLOSE,
            Permission.AUDIT_READ,
            Permission.ORG_MANAGE_USERS,
            Permission.CORRELATION_READ,
        }
    ),
    Role.SYSTEM_ADMIN: frozenset(
        {
            Permission.OBS_CREATE,
            Permission.OBS_READ_REDACTED,
            Permission.OBS_READ_RESTRICTED,
            Permission.OBS_CORRECT,
            Permission.OBS_QUALITY_FLAG,
            Permission.OBS_CLARIFY,
            Permission.OBS_HIDE,
            Permission.SOURCE_READ,
            Permission.EVIDENCE_UPLOAD,
            Permission.EVIDENCE_READ_DERIVATIVE,
            Permission.EVIDENCE_READ_ORIGINAL,
            Permission.EVIDENCE_READ_SCAN_STATUS,
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_ASSIGN,
            Permission.CASE_LINK_OBS,
            Permission.CASE_TRANSITION_BASIC,
            Permission.CASE_TRANSITION_CLOSE,
            Permission.AUDIT_READ,
            Permission.ORG_MANAGE_USERS,
            Permission.ADMIN_MANAGE_SYSTEM,
            Permission.JOBS_READ,
            Permission.CORRELATION_READ,
            Permission.CORRELATION_REVIEW,
        }
    ),
}

_ROLE_LABEL_PRECEDENCE: tuple[Role, ...] = (
    Role.SYSTEM_ADMIN,
    Role.ORGANISATION_ADMIN,
    Role.INTERVENTION_MANAGER,
    Role.ENVIRONMENTAL_SPECIALIST,
    Role.INVESTIGATOR,
    Role.REVIEWER,
    Role.REGISTERED_CONTRIBUTOR,
    Role.ANONYMOUS_CONTRIBUTOR,
)


@dataclass(frozen=True, slots=True)
class Principal:
    """Resolved security context for the current request."""

    userId: UUID | None = None
    systemRole: SystemRole | None = None
    memberships: tuple[tuple[UUID, Role], ...] = ()
    isAuthenticated: bool = False

    @property
    def is_system_admin(self) -> bool:
        """Return True when the principal holds the platform-wide system_admin role."""
        return self.isAuthenticated and self.systemRole == SystemRole.SYSTEM_ADMIN

    @property
    def primary_role_label(self) -> str:
        """Deterministic non-PII role label for audit trails and allowlisted logs."""
        if not self.isAuthenticated:
            return Role.ANONYMOUS_CONTRIBUTOR.value
        if self.is_system_admin:
            return Role.SYSTEM_ADMIN.value
        held = {role for _, role in self.memberships}
        for role in _ROLE_LABEL_PRECEDENCE:
            if role in held:
                return role.value
        return Role.REGISTERED_CONTRIBUTOR.value

    def roles_for_org(self, orgId: UUID) -> set[Role]:
        """Return all active roles held by the principal within the given organisation."""
        return {
            memberRole
            for memberOrgId, memberRole in self.memberships
            if memberOrgId == orgId
        }

    def accessible_org_ids(self, perm: Permission) -> set[UUID]:
        """Return organisation IDs where an explicit membership grants the permission."""
        return {
            orgId
            for orgId, role in self.memberships
            if perm in ROLE_PERMISSIONS.get(role, frozenset())
        }

    def has_permission(self, perm: Permission, orgId: UUID | None = None) -> bool:
        """Evaluate deny-by-default RBAC grant, optionally scoped to an organisation."""
        if not self.isAuthenticated:
            return perm in ROLE_PERMISSIONS[Role.ANONYMOUS_CONTRIBUTOR]
        if self.is_system_admin and perm in ROLE_PERMISSIONS[Role.SYSTEM_ADMIN]:
            return True
        if orgId is not None:
            return any(
                perm in ROLE_PERMISSIONS.get(role, frozenset())
                for role in self.roles_for_org(orgId)
            )
        if perm in ROLE_PERMISSIONS[Role.REGISTERED_CONTRIBUTOR]:
            return True
        return any(
            perm in ROLE_PERMISSIONS.get(role, frozenset()) for _, role in self.memberships
        )


def ensure_not_self_submitted(principal: Principal, submittedByUserId: UUID | None) -> None:
    """Prevent contributors from reviewing, verifying, or approving their own submission."""
    if (
        principal.userId is not None
        and submittedByUserId is not None
        and principal.userId == submittedByUserId
    ):
        raise DomainError(
            ErrorCode.SELF_REVIEW_FORBIDDEN,
            "Self-review or self-approval of your own submission is forbidden",
            statusCode=status.HTTP_403_FORBIDDEN,
        )
