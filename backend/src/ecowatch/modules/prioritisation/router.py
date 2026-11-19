"""FastAPI routes for transparent, evidence-honest prioritisation."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.prioritisation.schemas import (
    AssessmentResponse,
    CreateAssessmentRequest,
    RecordDecisionRequest,
)
from ecowatch.modules.prioritisation.service import PrioritisationService

router = APIRouter(prefix="/prioritisation", tags=["prioritisation"])


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: CreateAssessmentRequest,
    principal: Principal = Depends(require_permission(Permission.PRIORITISATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AssessmentResponse:
    """Record factors and gaps without imputing missing prioritisation inputs."""
    record = PrioritisationService(db).create_assessment(
        principal, **payload.model_dump(), requestId=requestId
    )
    return AssessmentResponse.model_validate(record)


@router.post("/assessments/{assessmentId}/decision", response_model=AssessmentResponse)
def record_decision(
    payload: RecordDecisionRequest,
    assessmentId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.PRIORITISATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AssessmentResponse:
    """Record one accountable human decision with its rationale."""
    record = PrioritisationService(db).record_decision(
        principal, assessmentId=assessmentId, **payload.model_dump(), requestId=requestId
    )
    return AssessmentResponse.model_validate(record)


@router.get("/assessments", response_model=CursorPage[AssessmentResponse])
def list_assessments(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.PRIORITISATION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[AssessmentResponse]:
    """List assessments and recorded decisions within the caller's organisations."""
    return PrioritisationService(db).list_assessments(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )
