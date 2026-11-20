"""Application service layer for cases, state transitions, observation links, and timelines."""

import base64
import json
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.cases.models import Case, CaseStatus, LinkProposedBy, LinkReviewStatus
from ecowatch.modules.cases.repository import CaseRepository
from ecowatch.modules.cases.schemas import (
    CaseActionResponse,
    CaseDetailResponse,
    CaseObservationResponse,
    CaseResponse,
    CreateCaseRequest,
    CrossCaseRequest,
    FieldVerificationApprovalRequest,
    FieldVerificationApprovalResponse,
    FieldVerificationApprovalRole,
    LinkObservationRequest,
    MergeCaseRequest,
    PromoteToCaseRequest,
    PublicCaseResponse,
    SplitCaseRequest,
    TimelineItemResponse,
    TransitionCaseStatusRequest,
    UpdateCaseObservationRequest,
    UpdateCaseRequest,
)
from ecowatch.modules.identity.models import User
from ecowatch.modules.identity.permissions import (
    Permission,
    Principal,
    Role,
    ensure_not_self_submitted,
)
from ecowatch.modules.identity.repository import IdentityRepository
from ecowatch.modules.verification import rules

_INITIAL_CASE_STATUSES = frozenset({CaseStatus.NEW_UNREVIEWED, CaseStatus.INITIAL_REVIEW})

_PHASE_1_DISABLED_STATUSES = frozenset(
    {
        CaseStatus.UNDER_INTERVENTION,
        CaseStatus.MONITORING_OUTCOMES,
        CaseStatus.RECOVERY_VERIFIED,
    }
)

_ALLOWED_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.NEW_UNREVIEWED: frozenset(
        {
            CaseStatus.INITIAL_REVIEW,
            CaseStatus.EVIDENCE_GATHERING,
            CaseStatus.FIELD_VERIFICATION_REQUIRED,
            CaseStatus.NOT_SUBSTANTIATED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.INITIAL_REVIEW: frozenset(
        {
            CaseStatus.EVIDENCE_GATHERING,
            CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE,
            CaseStatus.FIELD_VERIFICATION_REQUIRED,
            CaseStatus.REFERRED_TO_AUTHORITY,
            CaseStatus.NOT_SUBSTANTIATED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.EVIDENCE_GATHERING: frozenset(
        {
            CaseStatus.INITIAL_REVIEW,
            CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE,
            CaseStatus.FIELD_VERIFICATION_REQUIRED,
            CaseStatus.FIELD_VERIFIED,
            CaseStatus.REFERRED_TO_AUTHORITY,
            CaseStatus.NOT_SUBSTANTIATED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE: frozenset(
        {
            CaseStatus.EVIDENCE_GATHERING,
            CaseStatus.FIELD_VERIFICATION_REQUIRED,
            CaseStatus.FIELD_VERIFIED,
            CaseStatus.REFERRED_TO_AUTHORITY,
            CaseStatus.NOT_SUBSTANTIATED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.FIELD_VERIFICATION_REQUIRED: frozenset(
        {
            CaseStatus.EVIDENCE_GATHERING,
            CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE,
            CaseStatus.FIELD_VERIFIED,
            CaseStatus.REFERRED_TO_AUTHORITY,
            CaseStatus.NOT_SUBSTANTIATED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.FIELD_VERIFIED: frozenset(
        {
            CaseStatus.REFERRED_TO_AUTHORITY,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.REFERRED_TO_AUTHORITY: frozenset(
        {
            CaseStatus.FIELD_VERIFICATION_REQUIRED,
            CaseStatus.FIELD_VERIFIED,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.NOT_SUBSTANTIATED: frozenset(
        {
            CaseStatus.EVIDENCE_GATHERING,
            CaseStatus.CLOSED,
            CaseStatus.MERGED,
        }
    ),
    CaseStatus.CLOSED: frozenset(),
    CaseStatus.MERGED: frozenset(),
}

_STATUS_ALLOWED_ROLES: dict[CaseStatus, frozenset[Role]] = {
    CaseStatus.NEW_UNREVIEWED: frozenset(
        {Role.REVIEWER, Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}
    ),
    CaseStatus.INITIAL_REVIEW: frozenset(
        {Role.REVIEWER, Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}
    ),
    CaseStatus.EVIDENCE_GATHERING: frozenset(
        {Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}
    ),
    CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE: frozenset(
        {Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}
    ),
    CaseStatus.FIELD_VERIFICATION_REQUIRED: frozenset(
        {Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}
    ),
    CaseStatus.FIELD_VERIFIED: frozenset({Role.ENVIRONMENTAL_SPECIALIST, Role.ORGANISATION_ADMIN}),
    CaseStatus.REFERRED_TO_AUTHORITY: frozenset({Role.INVESTIGATOR, Role.ORGANISATION_ADMIN}),
    CaseStatus.NOT_SUBSTANTIATED: frozenset({Role.INVESTIGATOR, Role.ORGANISATION_ADMIN}),
    CaseStatus.CLOSED: frozenset({Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}),
    CaseStatus.MERGED: frozenset({Role.INVESTIGATOR, Role.ORGANISATION_ADMIN, Role.SYSTEM_ADMIN}),
}

_STATUS_REQUIRES_RATIONALE = frozenset(
    {
        CaseStatus.EVIDENCE_GATHERING,
        CaseStatus.CORROBORATED_EVIDENCE_AVAILABLE,
        CaseStatus.FIELD_VERIFICATION_REQUIRED,
        CaseStatus.NOT_SUBSTANTIATED,
        CaseStatus.CLOSED,
        CaseStatus.MERGED,
    }
)

_TERMINAL_CASE_STATUSES = frozenset({CaseStatus.CLOSED.value, CaseStatus.MERGED.value})

# ADR-034/ADR-035: case-side correlation actions are single-actor IV/OA/SA
# operations (org-scoped, self-review guarded, audited). The two-key ES+OA rule
# is reserved for §1.7 scientific conclusions (field_verified/recovery_verified).
_CASE_ACTION_ROLES = frozenset({Role.INVESTIGATOR, Role.ORGANISATION_ADMIN})

_INVESTIGATION_CONTENT_FIELDS = frozenset(
    {
        "title",
        "summary",
        "areaGeometry",
        "publicGeometry",
        "areaReference",
        "investigationQuestions",
        "competingHypotheses",
        "evidenceGaps",
        "fieldRecordReference",
        "referralRecord",
        "accessClass",
        "publicSummary",
    }
)

_ES_ALLOWED_UPDATE_FIELDS = frozenset(
    {
        "summary",
        "publicGeometry",
        "investigationQuestions",
        "competingHypotheses",
        "evidenceGaps",
        "fieldRecordReference",
        "publicSummary",
    }
)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _encode_timeline_cursor(item: TimelineItemResponse) -> str:
    payload = {
        "t": _as_utc(item.timestamp).isoformat(),
        "dt": item.dateType,
        "id": str(item.entityId),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_timeline_cursor(cursor: str) -> tuple[datetime, str, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        payload = json.loads(raw)
        timestamp = _as_utc(datetime.fromisoformat(payload["t"]))
        dateType = str(payload["dt"])
        entityId = str(uuid.UUID(payload["id"]))
        return timestamp, dateType, entityId
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid pagination cursor",
            statusCode=status.HTTP_400_BAD_REQUEST,
            field="cursor",
        ) from exc


class CaseService:
    """Domain service enforcing RBAC, org isolation, status machine, and audit logging."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = CaseRepository(session)

    def _require_authenticated_user(self, principal: Principal) -> uuid.UUID:
        if not principal.isAuthenticated or principal.userId is None:
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication required",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        return principal.userId

    def _effective_roles(self, principal: Principal, orgId: uuid.UUID) -> set[Role]:
        roles = set(principal.roles_for_org(orgId))
        if principal.is_system_admin:
            roles.add(Role.SYSTEM_ADMIN)
        return roles

    def _load_scoped_case(
        self, principal: Principal, caseId: uuid.UUID, *, requireNonTerminal: bool = False
    ) -> Case:
        case = self._repo.get_case(caseId)
        if case is None or (
            not principal.is_system_admin
            and not principal.has_permission(Permission.CASE_READ, case.organisationId)
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Case not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if requireNonTerminal and case.status in _TERMINAL_CASE_STATUSES:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "Cannot modify a closed or merged case",
                statusCode=status.HTTP_409_CONFLICT,
            )
        return case

    def _validate_assignee(self, userId: uuid.UUID, orgId: uuid.UUID) -> None:
        if not self._repo.user_exists(userId):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Lead investigator user not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="leadInvestigatorId",
            )
        if not self._repo.user_has_active_membership(userId, orgId):
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Lead investigator must belong to the case organisation",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="leadInvestigatorId",
            )

    def _generate_case_code(self) -> str:
        stamp = utc_now().strftime("%Y%m%d")
        for _ in range(5):
            candidate = f"CASE-{stamp}-{secrets.token_hex(4).upper()}"
            if self._repo.get_case_by_code(candidate) is None:
                return candidate
        return f"CASE-{stamp}-{uuid.uuid4().hex[:10].upper()}"

    def _ensure_not_observation_submitter(self, principal: Principal, caseId: uuid.UUID) -> None:
        links = self._repo.list_case_observations(caseId)
        obsIds = [link.observationId for link in links]
        for row in self._repo.list_observation_rows(obsIds):
            ensure_not_self_submitted(principal, row.get("submitted_by_user_id"))

    def create_case(
        self,
        principal: Principal,
        payload: CreateCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseResponse:
        """Create a new case independently of observations (RV/IV/OA/SA only)."""
        userId = self._require_authenticated_user(principal)
        if not self._repo.organisation_exists(payload.organisationId):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Organisation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="organisationId",
            )
        if not principal.has_permission(Permission.CASE_CREATE, payload.organisationId):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Missing permission to create cases for this organisation",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if payload.status not in _INITIAL_CASE_STATUSES:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "Initial case status must be new_unreviewed or initial_review",
                statusCode=status.HTTP_409_CONFLICT,
                field="status",
            )
        if payload.leadInvestigatorId is not None:
            if not principal.has_permission(Permission.CASE_ASSIGN, payload.organisationId):
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Missing permission to assign a lead investigator",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            self._validate_assignee(payload.leadInvestigatorId, payload.organisationId)

        if payload.caseCode is not None:
            if self._repo.get_case_by_code(payload.caseCode) is not None:
                raise DomainError(
                    ErrorCode.CONFLICT,
                    "A case with this caseCode already exists",
                    statusCode=status.HTTP_409_CONFLICT,
                    field="caseCode",
                )
            caseCode = payload.caseCode
        else:
            caseCode = self._generate_case_code()

        reviewedAt = utc_now() if payload.status == CaseStatus.INITIAL_REVIEW else None
        case = self._repo.create_case(
            organisationId=payload.organisationId,
            caseCode=caseCode,
            title=payload.title,
            summary=payload.summary,
            statusValue=payload.status.value,
            statusRationale=payload.statusRationale,
            areaGeometry=payload.areaGeometry,
            publicGeometry=payload.publicGeometry,
            areaReference=payload.areaReference,
            leadInvestigatorId=payload.leadInvestigatorId,
            investigationQuestions=payload.investigationQuestions,
            competingHypotheses=payload.competingHypotheses,
            evidenceGaps=payload.evidenceGaps,
            accessClass=payload.accessClass,
            publicSummary=payload.publicSummary,
            createdByUserId=userId,
            lastReviewedAt=reviewedAt,
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case.created",
            targetType="case",
            targetId=case.id,
            reason=case.statusRationale,
            details={"caseCode": case.caseCode, "status": case.status},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(case)
        return CaseResponse.model_validate(case)

    def list_cases(
        self,
        principal: Principal,
        *,
        organisationId: uuid.UUID | None = None,
        statusFilter: CaseStatus | None = None,
        leadInvestigatorId: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[CaseResponse]:
        """List cursor-paginated cases scoped strictly to the caller's organisations."""
        self._require_authenticated_user(principal)
        allowedOrgIds: set[uuid.UUID] | None = None
        if not principal.is_system_admin:
            allowedOrgIds = principal.accessible_org_ids(Permission.CASE_READ)
            if not allowedOrgIds:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Missing permission to read cases",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )

        items, nextCursor, hasMore = self._repo.list_cases(
            organisationIds=allowedOrgIds,
            organisationId=organisationId,
            statusFilter=statusFilter.value if statusFilter is not None else None,
            leadInvestigatorId=leadInvestigatorId,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[CaseResponse](
            items=[CaseResponse.model_validate(item) for item in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def get_case(self, principal: Principal, caseId: uuid.UUID) -> CaseDetailResponse:
        """Retrieve a single case with linked observation records (org-scoped)."""
        self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId)
        links = self._repo.list_case_observations(case.id)
        baseData = CaseResponse.model_validate(case).model_dump()
        return CaseDetailResponse(
            **baseData,
            observations=[CaseObservationResponse.model_validate(link) for link in links],
        )

    def update_case(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: UpdateCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseResponse:
        """Update case content, assignment, or public summary governance flags."""
        userId = self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId, requireNonTerminal=True)

        fieldsSet = payload.model_fields_set
        if not fieldsSet:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "At least one field must be provided for update",
                statusCode=status.HTTP_400_BAD_REQUEST,
            )

        orgRoles = principal.roles_for_org(case.organisationId)
        if "leadInvestigatorId" in fieldsSet:
            if not principal.has_permission(Permission.CASE_ASSIGN, case.organisationId):
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Missing permission to assign lead investigator",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            if payload.leadInvestigatorId is not None:
                self._validate_assignee(payload.leadInvestigatorId, case.organisationId)
            case.leadInvestigatorId = payload.leadInvestigatorId

        contentUpdates = fieldsSet & _INVESTIGATION_CONTENT_FIELDS
        if contentUpdates:
            self._enforce_content_update_authority(principal, case, orgRoles, contentUpdates)
            for fieldName in contentUpdates:
                setattr(case, fieldName, getattr(payload, fieldName))

        if "isPublicSummaryApproved" in fieldsSet:
            self._apply_public_summary_approval(
                principal, case, orgRoles, payload.isPublicSummaryApproved
            )

        case.lastReviewedAt = utc_now()
        self._session.flush()
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case.updated",
            targetType="case",
            targetId=case.id,
            details={"updatedFields": sorted(fieldsSet)},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(case)
        return CaseResponse.model_validate(case)

    def _enforce_content_update_authority(
        self,
        principal: Principal,
        case: Case,
        orgRoles: set[Role],
        contentUpdates: set[str],
    ) -> None:
        if not principal.has_permission(Permission.CASE_UPDATE, case.organisationId):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Missing permission to update case investigation fields",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        hasRv = Role.REVIEWER in orgRoles
        hasIv = Role.INVESTIGATOR in orgRoles
        hasEs = Role.ENVIRONMENTAL_SPECIALIST in orgRoles

        if (
            hasIv
            and not hasRv
            and not hasEs
            and case.leadInvestigatorId is not None
            and case.leadInvestigatorId != principal.userId
        ):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only the assigned investigator may update this case",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if hasEs and not hasRv and not hasIv and (contentUpdates - _ES_ALLOWED_UPDATE_FIELDS):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Environmental specialists may only update technical notes and public drafts",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

    def _apply_public_summary_approval(
        self,
        principal: Principal,
        case: Case,
        orgRoles: set[Role],
        approved: bool | None,
    ) -> None:
        if approved is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "isPublicSummaryApproved must be a boolean",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="isPublicSummaryApproved",
            )
        if approved:
            if (
                Role.ORGANISATION_ADMIN not in orgRoles
                and Role.ENVIRONMENTAL_SPECIALIST not in orgRoles
            ):
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Only organisation_admin or environmental_specialist "
                    "may approve public summaries",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            if not case.publicSummary:
                raise DomainError(
                    ErrorCode.VALIDATION_ERROR,
                    "publicSummary is required before approval",
                    statusCode=status.HTTP_400_BAD_REQUEST,
                    field="publicSummary",
                )
            case.isPublicSummaryApproved = True
            return

        if not principal.is_system_admin and Role.ORGANISATION_ADMIN not in orgRoles:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only organisation_admin or system_admin may unpublish a public summary",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        case.isPublicSummaryApproved = False

    def record_field_verification_approval(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: FieldVerificationApprovalRequest,
        *,
        requestId: str | None = None,
    ) -> FieldVerificationApprovalResponse:
        """Record one key (ES or OA) of the mandatory two-key field_verified approval."""
        userId = self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId, requireNonTerminal=True)

        orgRoles = principal.roles_for_org(case.organisationId)
        hasEs = Role.ENVIRONMENTAL_SPECIALIST in orgRoles
        hasOa = Role.ORGANISATION_ADMIN in orgRoles
        if not hasEs and not hasOa:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Field verification approval requires environmental_specialist "
                "or organisation_admin",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        self._ensure_not_observation_submitter(principal, case.id)
        chosenSlot = self._resolve_approval_slot(
            userId=userId,
            case=case,
            hasEs=hasEs,
            hasOa=hasOa,
            requestedRole=payload.approvalRole,
        )

        otherApprovalId = (
            case.authorityApprovalUserId
            if chosenSlot == FieldVerificationApprovalRole.SPECIALIST
            else case.specialistApprovalUserId
        )
        if otherApprovalId == userId:
            raise DomainError(
                ErrorCode.TWO_KEY_APPROVAL_REQUIRED,
                "Specialist and authority approvals must come from two distinct users",
                statusCode=status.HTTP_409_CONFLICT,
            )
        if chosenSlot == FieldVerificationApprovalRole.SPECIALIST:
            case.specialistApprovalUserId = userId
        else:
            case.authorityApprovalUserId = userId

        if payload.fieldRecordReference is not None:
            case.fieldRecordReference = payload.fieldRecordReference

        self._session.flush()
        ready = (
            case.specialistApprovalUserId is not None
            and case.authorityApprovalUserId is not None
            and case.specialistApprovalUserId != case.authorityApprovalUserId
            and bool(case.fieldRecordReference)
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case.field_verification_approved",
            targetType="case",
            targetId=case.id,
            reason=payload.rationale,
            details={
                "approvalRole": chosenSlot.value,
                "readyForFieldVerified": ready,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(case)
        return FieldVerificationApprovalResponse(
            caseId=case.id,
            status=CaseStatus(case.status),
            fieldRecordReference=case.fieldRecordReference,
            specialistApprovalUserId=case.specialistApprovalUserId,
            authorityApprovalUserId=case.authorityApprovalUserId,
            readyForFieldVerified=ready,
        )

    def _resolve_approval_slot(
        self,
        *,
        userId: uuid.UUID,
        case: Case,
        hasEs: bool,
        hasOa: bool,
        requestedRole: FieldVerificationApprovalRole | None,
    ) -> FieldVerificationApprovalRole:
        if requestedRole == FieldVerificationApprovalRole.SPECIALIST:
            if not hasEs:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Caller does not hold environmental_specialist role in this organisation",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            return FieldVerificationApprovalRole.SPECIALIST
        if requestedRole == FieldVerificationApprovalRole.AUTHORITY:
            if not hasOa:
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Caller does not hold organisation_admin role in this organisation",
                    statusCode=status.HTTP_403_FORBIDDEN,
                )
            return FieldVerificationApprovalRole.AUTHORITY
        if hasEs and not hasOa:
            return FieldVerificationApprovalRole.SPECIALIST
        if hasOa and not hasEs:
            return FieldVerificationApprovalRole.AUTHORITY
        if case.specialistApprovalUserId is None and case.authorityApprovalUserId != userId:
            return FieldVerificationApprovalRole.SPECIALIST
        if case.authorityApprovalUserId is None and case.specialistApprovalUserId != userId:
            return FieldVerificationApprovalRole.AUTHORITY
        raise DomainError(
            ErrorCode.TWO_KEY_APPROVAL_REQUIRED,
            "Two-key approval requires two distinct users (ES and OA)",
            statusCode=status.HTTP_409_CONFLICT,
        )

    def transition_status(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: TransitionCaseStatusRequest,
        *,
        requestId: str | None = None,
    ) -> CaseResponse:
        """Advance case status enforcing Phase 1 transition graph, RBAC, and two-key rules."""
        userId = self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId)
        currentStatus = CaseStatus(case.status)
        targetStatus = payload.status

        if targetStatus in _PHASE_1_DISABLED_STATUSES:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                f"Status '{targetStatus.value}' is not enabled in Phase 1",
                statusCode=status.HTTP_409_CONFLICT,
                field="status",
            )
        if targetStatus not in _ALLOWED_TRANSITIONS.get(currentStatus, frozenset()):
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                f"Cannot transition case from '{currentStatus.value}' to '{targetStatus.value}'",
                statusCode=status.HTTP_409_CONFLICT,
                field="status",
            )

        effectiveRoles = self._effective_roles(principal, case.organisationId)
        if not (effectiveRoles & _STATUS_ALLOWED_ROLES[targetStatus]):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                f"Missing authority to transition case to '{targetStatus.value}'",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        if targetStatus in _STATUS_REQUIRES_RATIONALE and not payload.statusRationale:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"statusRationale is required for status '{targetStatus.value}'",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="statusRationale",
            )

        auditDetails: dict[str, Any] = {
            "fromStatus": currentStatus.value,
            "toStatus": targetStatus.value,
        }

        if targetStatus == CaseStatus.REFERRED_TO_AUTHORITY:
            referral = payload.referralRecord or case.referralRecord
            if not referral:
                raise DomainError(
                    ErrorCode.VALIDATION_ERROR,
                    "referralRecord is required when referring a case to an authority",
                    statusCode=status.HTTP_400_BAD_REQUEST,
                    field="referralRecord",
                )
            case.referralRecord = referral

        if targetStatus == CaseStatus.FIELD_VERIFIED:
            self._complete_field_verified_transition(
                principal=principal,
                userId=userId,
                case=case,
                payload=payload,
            )
            auditDetails["fieldRecordReference"] = case.fieldRecordReference
            auditDetails["specialistApproverUserId"] = str(case.specialistApproverUserId)
            auditDetails["authorityApproverUserId"] = str(case.authorityApproverUserId)

        if targetStatus == CaseStatus.MERGED:
            targetCase = self._validate_merge_target(case, payload.mergedIntoCaseId)
            case.mergedIntoCaseId = targetCase.id
            auditDetails["mergedIntoCaseId"] = str(targetCase.id)

        case.status = targetStatus.value
        if payload.statusRationale is not None:
            case.statusRationale = payload.statusRationale
        case.lastReviewedAt = utc_now()

        self._session.flush()
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case.status_changed",
            targetType="case",
            targetId=case.id,
            reason=payload.statusRationale,
            details=auditDetails,
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(case)
        return CaseResponse.model_validate(case)

    def _validate_merge_target(self, case: Case, mergedIntoCaseId: uuid.UUID | None) -> Case:
        if mergedIntoCaseId is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "mergedIntoCaseId is required when merging a case",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="mergedIntoCaseId",
            )
        if mergedIntoCaseId == case.id:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "A case cannot be merged into itself",
                statusCode=status.HTTP_409_CONFLICT,
                field="mergedIntoCaseId",
            )
        targetCase = self._repo.get_case(mergedIntoCaseId)
        if targetCase is None or targetCase.organisationId != case.organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Target case not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="mergedIntoCaseId",
            )
        if targetCase.status == CaseStatus.MERGED.value:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "Cannot merge into a case that is already merged",
                statusCode=status.HTTP_409_CONFLICT,
                field="mergedIntoCaseId",
            )
        return targetCase

    def _roles_in_org(self, userId: uuid.UUID | None, organisationId: uuid.UUID) -> frozenset[Role]:
        """Return active roles a recorded approver holds in the case organisation."""
        if userId is None:
            return frozenset()
        user = self._session.get(User, userId)
        if user is None or not user.isActive:
            return frozenset()
        memberships = IdentityRepository(self._session).list_active_memberships_for_user(userId)
        return frozenset(
            Role(item.role) for item in memberships if item.organisationId == organisationId
        )

    def _case_owner_ids(self, case: Case) -> frozenset[uuid.UUID]:
        """Return case creator, lead, and linked-observation submitters excluded from approval."""
        ownerIds = {case.createdByUserId}
        if case.leadInvestigatorId is not None:
            ownerIds.add(case.leadInvestigatorId)
        obsIds = [link.observationId for link in self._repo.list_case_observations(case.id)]
        for row in self._repo.list_observation_rows(obsIds):
            submitterId = row.get("submitted_by_user_id")
            if submitterId is not None:
                ownerIds.add(submitterId)
        return frozenset(ownerIds)

    def _complete_field_verified_transition(
        self,
        *,
        principal: Principal,
        userId: uuid.UUID,
        case: Case,
        payload: TransitionCaseStatusRequest,
    ) -> None:
        orgRoles = principal.roles_for_org(case.organisationId)
        if not orgRoles & {Role.ENVIRONMENTAL_SPECIALIST, Role.ORGANISATION_ADMIN}:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "field_verified requires environmental_specialist and organisation_admin approval",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        self._ensure_not_observation_submitter(principal, case.id)

        fieldRef = payload.fieldRecordReference or case.fieldRecordReference
        if not fieldRef:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "fieldRecordReference is required for field_verified",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="fieldRecordReference",
            )
        case.fieldRecordReference = fieldRef

        specialistId = payload.specialistApproverUserId
        authorityId = payload.authorityApproverUserId
        rules.assert_two_key_pair(
            specialistApproverUserId=specialistId,
            authorityApproverUserId=authorityId,
            actorUserId=userId,
            specialistRoles=self._roles_in_org(specialistId, case.organisationId),
            authorityRoles=self._roles_in_org(authorityId, case.organisationId),
            interventionOwnerUserIds=self._case_owner_ids(case),
            errorCode=ErrorCode.TWO_KEY_APPROVAL_REQUIRED,
        )
        approvedAt = utc_now()
        case.specialistApproverUserId = specialistId
        case.authorityApproverUserId = authorityId
        case.twoKeyApprovedAt = approvedAt
        case.specialistApprovalUserId = specialistId
        case.authorityApprovalUserId = authorityId

    def link_observation(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: LinkObservationRequest,
        *,
        requestId: str | None = None,
    ) -> CaseObservationResponse:
        """Link an existing observation in the same organisation to a case (M:N)."""
        userId = self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId, requireNonTerminal=True)
        if not principal.has_permission(Permission.CASE_LINK_OBS, case.organisationId):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Missing permission to link observations to cases",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        obsRow = self._repo.lookup_observation(payload.observationId)
        if obsRow is None or obsRow.get("organisation_id") != case.organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="observationId",
            )

        ensure_not_self_submitted(principal, obsRow.get("submitted_by_user_id"))

        if self._repo.get_case_observation(case.id, payload.observationId) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "Observation is already linked to this case",
                statusCode=status.HTTP_409_CONFLICT,
                field="observationId",
            )

        isContested = payload.isContested or payload.reviewStatus == LinkReviewStatus.CONTESTED
        reviewStatus = LinkReviewStatus.CONTESTED if isContested else payload.reviewStatus
        if isContested and not payload.contestedNote:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "contestedNote is required when marking a link contested",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="contestedNote",
            )

        link = self._repo.create_case_observation(
            caseId=case.id,
            observationId=payload.observationId,
            linkRationale=payload.linkRationale,
            proposedByType=payload.proposedByType.value,
            proposedByUserId=userId,
            reviewStatus=reviewStatus.value,
            reviewedByUserId=userId,
            reviewedAt=utc_now(),
            isContested=isContested,
            contestedNote=payload.contestedNote,
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case_observation.linked",
            targetType="case_observation",
            targetId=link.id,
            reason=link.linkRationale,
            details={
                "caseId": str(case.id),
                "observationId": str(payload.observationId),
                "reviewStatus": link.reviewStatus,
                "isContested": link.isContested,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(link)
        return CaseObservationResponse.model_validate(link)

    def update_case_observation(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        observationId: uuid.UUID,
        payload: UpdateCaseObservationRequest,
        *,
        requestId: str | None = None,
    ) -> CaseObservationResponse:
        """Update review status, rationale, or contested flag on a case-observation link."""
        userId = self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId, requireNonTerminal=True)
        if not principal.has_permission(Permission.CASE_LINK_OBS, case.organisationId):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Missing permission to update case observation links",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

        link = self._repo.get_case_observation(case.id, observationId)
        if link is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Case observation link not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        obsRow = self._repo.lookup_observation(observationId)
        if obsRow is not None:
            ensure_not_self_submitted(principal, obsRow.get("submitted_by_user_id"))

        fieldsSet = payload.model_fields_set
        if not fieldsSet:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "At least one field must be provided for update",
                statusCode=status.HTTP_400_BAD_REQUEST,
            )

        if payload.linkRationale is not None:
            link.linkRationale = payload.linkRationale
        if "contestedNote" in fieldsSet:
            link.contestedNote = payload.contestedNote

        nextReview = (
            payload.reviewStatus
            if payload.reviewStatus is not None
            else LinkReviewStatus(link.reviewStatus)
        )
        nextContested = payload.isContested if payload.isContested is not None else link.isContested
        if (
            payload.reviewStatus in {LinkReviewStatus.ACCEPTED, LinkReviewStatus.REJECTED}
            and "isContested" not in fieldsSet
        ):
            nextContested = False
        if nextReview == LinkReviewStatus.CONTESTED or nextContested:
            nextReview = LinkReviewStatus.CONTESTED
            nextContested = True
            if not link.contestedNote:
                raise DomainError(
                    ErrorCode.VALIDATION_ERROR,
                    "contestedNote is required when marking a link contested",
                    statusCode=status.HTTP_400_BAD_REQUEST,
                    field="contestedNote",
                )

        link.reviewStatus = nextReview.value
        link.isContested = nextContested
        link.reviewedByUserId = userId
        link.reviewedAt = utc_now()

        self._session.flush()
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=case.organisationId,
            action="case_observation.updated",
            targetType="case_observation",
            targetId=link.id,
            reason=link.linkRationale,
            details={
                "caseId": str(case.id),
                "observationId": str(observationId),
                "reviewStatus": link.reviewStatus,
                "isContested": link.isContested,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(link)
        return CaseObservationResponse.model_validate(link)

    def _collect_observation_timeline(self, obsIds: list[uuid.UUID]) -> list[TimelineItemResponse]:
        items: list[TimelineItemResponse] = []
        for obs in self._repo.list_observation_rows(obsIds):
            obsId = obs["id"]
            timePrecision = str(obs.get("time_precision") or "unknown")
            obsSource = str(obs.get("source_type") or "observation")
            obsType = str(obs.get("observation_type") or "observation")
            obsSpecs = (
                (
                    "event_start_at",
                    timePrecision,
                    f"observation:{obsSource}",
                    f"Estimated start ({obsType})",
                ),
                (
                    "observed_at",
                    timePrecision,
                    f"observation:{obsSource}",
                    f"Observed ({obsType})",
                ),
                ("submitted_at", "exact", "observation_submission", f"Submitted ({obsType})"),
                ("received_at", "exact", "server_receipt", f"Server receipt ({obsType})"),
            )
            for colName, precision, source, summary in obsSpecs:
                ts = obs.get(colName)
                if ts is None:
                    continue
                items.append(
                    TimelineItemResponse(
                        dateType=colName,
                        timestamp=_as_utc(ts),
                        precision=precision,
                        source=source,
                        entityType="observation",
                        entityId=obsId,
                        summary=summary,
                    )
                )
        return items

    def _collect_evidence_timeline(self, obsIds: list[uuid.UUID]) -> list[TimelineItemResponse]:
        items: list[TimelineItemResponse] = []
        for asset in self._repo.list_evidence_rows_for_observations(obsIds):
            ts = asset.get("received_at") or asset.get("created_at")
            if ts is None:
                continue
            mediaLabel = asset.get("mime_type") or asset.get("media_type") or "evidence"
            items.append(
                TimelineItemResponse(
                    dateType="evidence_received_at",
                    timestamp=_as_utc(ts),
                    precision="exact",
                    source="evidence_asset",
                    entityType="evidence_asset",
                    entityId=asset["id"],
                    summary=f"Evidence received ({mediaLabel})",
                )
            )
        return items

    def _collect_audit_timeline(
        self, caseId: uuid.UUID, linkIds: list[uuid.UUID]
    ) -> list[TimelineItemResponse]:
        items: list[TimelineItemResponse] = []
        for event in self._repo.list_case_audit_rows(caseId, linkIds):
            ts = event.get("occurred_at")
            if ts is None:
                continue
            action = str(event.get("action") or "audit_event")
            actorRole = str(event.get("actor_role") or "system")
            items.append(
                TimelineItemResponse(
                    dateType=action,
                    timestamp=_as_utc(ts),
                    precision="exact",
                    source=f"audit:{actorRole}",
                    entityType=str(event.get("target_type") or "case"),
                    entityId=event["target_id"],
                    summary=event.get("reason"),
                )
            )
        return items

    def get_timeline(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> CursorPage[TimelineItemResponse]:
        """Aggregate chronological timeline items across observations, evidence, and audit."""
        self._require_authenticated_user(principal)
        case = self._load_scoped_case(principal, caseId)
        links = self._repo.list_case_observations(case.id)
        obsIds = [link.observationId for link in links]
        linkIds = [link.id for link in links]

        items = [
            *self._collect_observation_timeline(obsIds),
            *self._collect_evidence_timeline(obsIds),
            *self._collect_audit_timeline(case.id, linkIds),
        ]
        items.sort(key=lambda item: (item.timestamp, item.dateType, str(item.entityId)))

        if cursor is not None:
            cursorKey = _decode_timeline_cursor(cursor)
            items = [
                item
                for item in items
                if (item.timestamp, item.dateType, str(item.entityId)) > cursorKey
            ]

        hasMore = len(items) > limit
        pageItems = items[:limit]
        nextCursor = _encode_timeline_cursor(pageItems[-1]) if hasMore and pageItems else None
        return CursorPage[TimelineItemResponse](
            items=pageItems,
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_public_cases(
        self,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[PublicCaseResponse]:
        """Return approved, redacted public case summaries without contributor PII."""
        items, nextCursor, hasMore = self._repo.list_public_cases(cursor=cursor, limit=limit)
        return CursorPage[PublicCaseResponse](
            items=[PublicCaseResponse.model_validate(item) for item in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def get_public_case(self, caseId: uuid.UUID) -> PublicCaseResponse:
        """Return a single approved, redacted public case summary or 404."""
        case = self._repo.get_public_case(caseId)
        if case is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Public case summary not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return PublicCaseResponse.model_validate(case)

    # ------------------------------------------------------------------
    # ADR-031 case-side correlation actions (single-actor IV/OA/SA authority)
    # ------------------------------------------------------------------

    def _require_case_action_actor(
        self, principal: Principal, organisationId: uuid.UUID
    ) -> uuid.UUID:
        """Require an IV/OA/SA actor scoped to the organisation (404 across orgs)."""
        userId = self._require_authenticated_user(principal)
        if principal.is_system_admin:
            return userId
        orgRoles = principal.roles_for_org(organisationId)
        if not orgRoles:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Resource not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if not orgRoles & _CASE_ACTION_ROLES:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Case-side correlation actions require investigator, "
                "organisation_admin or system_admin authority",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        return userId

    def _ensure_not_submitter_of(
        self, principal: Principal, observationIds: list[uuid.UUID]
    ) -> None:
        """Block an actor from acting on their own submitted observations."""
        for row in self._repo.list_observation_rows(observationIds):
            ensure_not_self_submitted(principal, row.get("submitted_by_user_id"))

    def _action_result(
        self, action: str, case: Case, affectedObservationIds: list[uuid.UUID]
    ) -> CaseActionResponse:
        links = self._repo.list_case_observations(case.id)
        return CaseActionResponse(
            action=action,
            case=CaseDetailResponse(
                **CaseResponse.model_validate(case).model_dump(),
                observations=[CaseObservationResponse.model_validate(link) for link in links],
            ),
            affectedObservationIds=affectedObservationIds,
        )

    def _resolve_case_code(self, requested: str | None) -> str:
        if requested is not None:
            if self._repo.get_case_by_code(requested) is not None:
                raise DomainError(
                    ErrorCode.CONFLICT,
                    "A case with this caseCode already exists",
                    statusCode=status.HTTP_409_CONFLICT,
                    field="caseCode",
                )
            return requested
        return self._generate_case_code()

    def promote_to_case(
        self,
        principal: Principal,
        payload: PromoteToCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseActionResponse:
        """Promote a reviewed provisional cluster into a case with its members linked."""
        cluster = self._repo.get_cluster_for_action(payload.clusterId)
        if cluster is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Cluster not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="clusterId",
            )
        organisationId, memberIds = cluster
        userId = self._require_case_action_actor(principal, organisationId)
        if not memberIds:
            raise DomainError(
                ErrorCode.CONFLICT,
                "Cannot promote a cluster with no observations",
                statusCode=status.HTTP_409_CONFLICT,
                field="clusterId",
            )
        self._ensure_not_submitter_of(principal, memberIds)

        case = self._repo.create_case(
            organisationId=organisationId,
            caseCode=self._resolve_case_code(payload.caseCode),
            title=payload.title,
            summary=payload.summary,
            statusValue=CaseStatus.NEW_UNREVIEWED.value,
            statusRationale=payload.statusRationale,
            areaGeometry=None,
            publicGeometry=None,
            areaReference=None,
            leadInvestigatorId=None,
            investigationQuestions=[],
            competingHypotheses=[],
            evidenceGaps=[],
            accessClass=payload.accessClass,
            publicSummary=None,
            createdByUserId=userId,
            lastReviewedAt=utc_now(),
        )
        for observationId in memberIds:
            self._repo.create_case_observation(
                caseId=case.id,
                observationId=observationId,
                linkRationale=f"Promoted from cluster {payload.clusterId}",
                proposedByType=LinkProposedBy.HUMAN.value,
                proposedByUserId=userId,
                reviewStatus=LinkReviewStatus.ACCEPTED.value,
                reviewedByUserId=userId,
                reviewedAt=utc_now(),
                isContested=False,
                contestedNote=None,
            )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=organisationId,
            action="case.promoted_from_cluster",
            targetType="case",
            targetId=case.id,
            reason=payload.statusRationale,
            details={
                "clusterId": str(payload.clusterId),
                "promotedObservationCount": len(memberIds),
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(case)
        return self._action_result("promote_to_case", case, memberIds)

    def merge_cases(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: MergeCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseActionResponse:
        """Move all links from a source case into a target case, keeping both audited."""
        source = self._load_scoped_case(principal, caseId, requireNonTerminal=True)
        userId = self._require_case_action_actor(principal, source.organisationId)
        target = self._validate_merge_target(source, payload.targetCaseId)
        sourceLinks = self._repo.list_case_observations(source.id)
        self._ensure_not_submitter_of(principal, [link.observationId for link in sourceLinks])

        targetObservationIds = {
            link.observationId for link in self._repo.list_case_observations(target.id)
        }
        moved: list[uuid.UUID] = []
        deduplicated: list[uuid.UUID] = []
        for link in sourceLinks:
            if link.observationId in targetObservationIds:
                self._repo.delete_case_observation(link.id)
                deduplicated.append(link.observationId)
            else:
                self._repo.move_case_observation(link.id, target.id)
                moved.append(link.observationId)

        source.status = CaseStatus.MERGED.value
        source.mergedIntoCaseId = target.id
        source.statusRationale = payload.statusRationale
        source.lastReviewedAt = utc_now()

        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=source.organisationId,
            action="case.merged",
            targetType="case",
            targetId=source.id,
            reason=payload.statusRationale,
            details={
                "mergedIntoCaseId": str(target.id),
                "movedObservationIds": [str(obsId) for obsId in moved],
                "deduplicatedObservationIds": [str(obsId) for obsId in deduplicated],
            },
            requestId=requestId,
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=target.organisationId,
            action="case.merge_received",
            targetType="case",
            targetId=target.id,
            reason=payload.statusRationale,
            details={
                "sourceCaseId": str(source.id),
                "receivedObservationIds": [str(obsId) for obsId in moved],
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(target)
        return self._action_result("merge", target, moved)

    def split_case(
        self,
        principal: Principal,
        caseId: uuid.UUID,
        payload: SplitCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseActionResponse:
        """Move selected links from a case into a newly created case in the same org."""
        source = self._load_scoped_case(principal, caseId, requireNonTerminal=True)
        userId = self._require_case_action_actor(principal, source.organisationId)

        requested = list(dict.fromkeys(payload.observationIds))
        sourceLinks = self._repo.list_case_observations(source.id)
        linksByObservation = {link.observationId: link for link in sourceLinks}
        missing = [obsId for obsId in requested if obsId not in linksByObservation]
        if missing:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation is not linked to this case",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="observationIds",
            )
        self._ensure_not_submitter_of(principal, requested)

        newCase = self._repo.create_case(
            organisationId=source.organisationId,
            caseCode=self._resolve_case_code(payload.caseCode),
            title=payload.title,
            summary=payload.summary,
            statusValue=CaseStatus.NEW_UNREVIEWED.value,
            statusRationale=payload.statusRationale,
            areaGeometry=None,
            publicGeometry=None,
            areaReference=None,
            leadInvestigatorId=None,
            investigationQuestions=[],
            competingHypotheses=[],
            evidenceGaps=[],
            accessClass=source.accessClass,
            publicSummary=None,
            createdByUserId=userId,
            lastReviewedAt=utc_now(),
        )
        for observationId in requested:
            self._repo.move_case_observation(linksByObservation[observationId].id, newCase.id)

        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=source.organisationId,
            action="case.split_source",
            targetType="case",
            targetId=source.id,
            reason=payload.statusRationale,
            details={
                "newCaseId": str(newCase.id),
                "movedObservationIds": [str(obsId) for obsId in requested],
            },
            requestId=requestId,
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=newCase.organisationId,
            action="case.split_created",
            targetType="case",
            targetId=newCase.id,
            reason=payload.statusRationale,
            details={
                "sourceCaseId": str(source.id),
                "movedObservationIds": [str(obsId) for obsId in requested],
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(newCase)
        return self._action_result("split", newCase, requested)

    def cross_case(
        self,
        principal: Principal,
        payload: CrossCaseRequest,
        *,
        requestId: str | None = None,
    ) -> CaseActionResponse:
        """Move a selected subset of links between two cases in the same organisation."""
        source = self._load_scoped_case(principal, payload.sourceCaseId, requireNonTerminal=True)
        target = self._load_scoped_case(principal, payload.targetCaseId, requireNonTerminal=True)
        if source.organisationId != target.organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Target case not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="targetCaseId",
            )
        if source.id == target.id:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Source and target cases must differ",
                statusCode=status.HTTP_400_BAD_REQUEST,
                field="targetCaseId",
            )
        userId = self._require_case_action_actor(principal, source.organisationId)

        requested = list(dict.fromkeys(payload.observationIds))
        linksByObservation = {
            link.observationId: link for link in self._repo.list_case_observations(source.id)
        }
        missing = [obsId for obsId in requested if obsId not in linksByObservation]
        if missing:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation is not linked to the source case",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="observationIds",
            )
        self._ensure_not_submitter_of(principal, requested)

        targetObservationIds = {
            link.observationId for link in self._repo.list_case_observations(target.id)
        }
        moved: list[uuid.UUID] = []
        deduplicated: list[uuid.UUID] = []
        for observationId in requested:
            if observationId in targetObservationIds:
                self._repo.delete_case_observation(linksByObservation[observationId].id)
                deduplicated.append(observationId)
            else:
                sourceLink = linksByObservation[observationId]
                sourceLink.linkRationale = payload.linkRationale
                self._repo.move_case_observation(sourceLink.id, target.id)
                moved.append(observationId)

        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=source.organisationId,
            action="case.cross_case_moved",
            targetType="case",
            targetId=target.id,
            reason=payload.linkRationale,
            details={
                "sourceCaseId": str(source.id),
                "movedObservationIds": [str(obsId) for obsId in moved],
                "deduplicatedObservationIds": [str(obsId) for obsId in deduplicated],
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(target)
        return self._action_result("cross_case", target, moved)
