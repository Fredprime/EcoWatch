"""FastAPI routes for investigation cases, observation links, timelines, and public summaries."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import (
    get_current_principal,
    get_request_id,
    require_permission,
)
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.cases.models import CaseStatus
from ecowatch.modules.cases.schemas import (
    CaseDetailResponse,
    CaseObservationResponse,
    CaseResponse,
    CreateCaseRequest,
    FieldVerificationApprovalRequest,
    FieldVerificationApprovalResponse,
    LinkObservationRequest,
    PublicCaseResponse,
    TimelineItemResponse,
    TransitionCaseStatusRequest,
    UpdateCaseObservationRequest,
    UpdateCaseRequest,
)
from ecowatch.modules.cases.service import CaseService
from ecowatch.modules.identity.permissions import Permission, Principal

router = APIRouter(tags=["cases"])


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CreateCaseRequest,
    principal: Principal = Depends(require_permission(Permission.CASE_CREATE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> CaseResponse:
    """Create a new environmental investigation case (RV/IV/OA/SA only)."""
    return CaseService(db).create_case(principal, payload, requestId=requestId)


@router.get("/cases", response_model=CursorPage[CaseResponse])
def list_cases(
    organisationId: uuid.UUID | None = Query(default=None),
    caseStatus: CaseStatus | None = Query(default=None, alias="status"),
    leadInvestigatorId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.CASE_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[CaseResponse]:
    """List cursor-paginated cases scoped strictly to the caller's organisation(s)."""
    return CaseService(db).list_cases(
        principal,
        organisationId=organisationId,
        statusFilter=caseStatus,
        leadInvestigatorId=leadInvestigatorId,
        cursor=cursor,
        limit=limit,
    )


@router.get("/cases/{caseId}", response_model=CaseDetailResponse)
def get_case(
    caseId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.CASE_READ)),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    """Retrieve a single case and its linked observations (404 across organisations)."""
    return CaseService(db).get_case(principal, caseId)


@router.patch("/cases/{caseId}", response_model=CaseResponse)
def update_case(
    payload: UpdateCaseRequest,
    caseId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> CaseResponse:
    """Update case investigation fields, investigator assignment, or public summary approval."""
    return CaseService(db).update_case(principal, caseId, payload, requestId=requestId)


@router.post("/cases/{caseId}/status", response_model=CaseResponse)
def transition_case_status(
    payload: TransitionCaseStatusRequest,
    caseId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> CaseResponse:
    """Transition a case's lifecycle status with Phase 1 state machine and RBAC checks."""
    return CaseService(db).transition_status(principal, caseId, payload, requestId=requestId)


@router.post(
    "/cases/{caseId}/field-verification-approvals",
    response_model=FieldVerificationApprovalResponse,
)
def approve_field_verification(
    payload: FieldVerificationApprovalRequest,
    caseId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> FieldVerificationApprovalResponse:
    """Record an ES or OA sign-off toward the two-key field_verified requirement."""
    return CaseService(db).record_field_verification_approval(
        principal, caseId, payload, requestId=requestId
    )


@router.post(
    "/cases/{caseId}/observations",
    response_model=CaseObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_observation_to_case(
    payload: LinkObservationRequest,
    caseId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.CASE_LINK_OBS)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> CaseObservationResponse:
    """Link an observation in the same organisation to a case with rationale."""
    return CaseService(db).link_observation(principal, caseId, payload, requestId=requestId)


@router.patch(
    "/cases/{caseId}/observations/{observationId}",
    response_model=CaseObservationResponse,
)
def update_case_observation_link(
    payload: UpdateCaseObservationRequest,
    caseId: uuid.UUID = Path(),
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.CASE_LINK_OBS)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> CaseObservationResponse:
    """Update review status or contested state on an existing case-observation link."""
    return CaseService(db).update_case_observation(
        principal, caseId, observationId, payload, requestId=requestId
    )


@router.get("/cases/{caseId}/timeline", response_model=CursorPage[TimelineItemResponse])
def get_case_timeline(
    caseId: uuid.UUID = Path(),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    principal: Principal = Depends(require_permission(Permission.CASE_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[TimelineItemResponse]:
    """Return a chronological timeline distinguishing observation, evidence, and audit dates."""
    return CaseService(db).get_timeline(principal, caseId, cursor=cursor, limit=limit)


@router.get("/public/cases", response_model=CursorPage[PublicCaseResponse])
def list_public_cases(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> CursorPage[PublicCaseResponse]:
    """List approved public case summaries with internal and identity data stripped."""
    return CaseService(db).list_public_cases(cursor=cursor, limit=limit)


@router.get("/public/cases/{caseId}", response_model=PublicCaseResponse)
def get_public_case(
    caseId: uuid.UUID = Path(),
    db: Session = Depends(get_db),
) -> PublicCaseResponse:
    """Return a single approved public case summary or 404."""
    return CaseService(db).get_public_case(caseId)
