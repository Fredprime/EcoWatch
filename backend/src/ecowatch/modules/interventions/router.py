"""FastAPI routes for the intervention lifecycle and activity-only derivation."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.interventions.schemas import (
    AddMilestoneRequest,
    CompleteMilestoneRequest,
    CreateInterventionRequest,
    InterventionResponse,
    MilestoneResponse,
    TransitionInterventionRequest,
)
from ecowatch.modules.interventions.service import InterventionsService

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.post(
    "/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED
)
def create_intervention(
    payload: CreateInterventionRequest,
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> InterventionResponse:
    """Create a proposed intervention with accountable organisation and lead."""
    record = InterventionsService(db).create_intervention(
        principal, **payload.model_dump(), requestId=requestId
    )
    return InterventionResponse.model_validate(record)


@router.post(
    "/interventions/{interventionId}/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_milestone(
    payload: AddMilestoneRequest,
    interventionId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> MilestoneResponse:
    """Add a planned milestone to an in-scope intervention."""
    record = InterventionsService(db).add_milestone(
        principal, interventionId=interventionId, **payload.model_dump(), requestId=requestId
    )
    return MilestoneResponse.model_validate(record)


@router.post("/milestones/{milestoneId}/complete", response_model=MilestoneResponse)
def complete_milestone(
    payload: CompleteMilestoneRequest,
    milestoneId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> MilestoneResponse:
    """Complete a milestone; only activity status can be derived from it."""
    record = InterventionsService(db).complete_milestone(
        principal, milestoneId=milestoneId, **payload.model_dump(), requestId=requestId
    )
    return MilestoneResponse.model_validate(record)


@router.post("/interventions/{interventionId}/transition", response_model=InterventionResponse)
def transition_intervention(
    payload: TransitionInterventionRequest,
    interventionId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> InterventionResponse:
    """Apply an explicit status transition with rationale and recovery gate."""
    record = InterventionsService(db).transition(
        principal, interventionId=interventionId, **payload.model_dump(), requestId=requestId
    )
    return InterventionResponse.model_validate(record)


@router.get("/interventions", response_model=CursorPage[InterventionResponse])
def list_interventions(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[InterventionResponse]:
    """List interventions with their recorded status and accountable owner."""
    return InterventionsService(db).list_interventions(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get(
    "/interventions/{interventionId}/milestones", response_model=CursorPage[MilestoneResponse]
)
def list_milestones(
    interventionId: uuid.UUID = Path(),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTERVENTION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[MilestoneResponse]:
    """List delivery milestones of one in-scope intervention."""
    return InterventionsService(db).list_milestones(
        principal, interventionId, cursor=cursor, limit=limit
    )
