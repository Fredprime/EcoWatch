"""FastAPI routes for environmental entities, analyses, and the prediction gate."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.intelligence.schemas import (
    AnalysisOutputResponse,
    AnalysisRunResponse,
    CreateEntityRequest,
    EntityResponse,
    PredictionCheckRequest,
    PredictionCheckResponse,
    ProposeRelationshipRequest,
    QueueAnalysisRequest,
    RecordAnalysisOutputRequest,
    RelationshipResponse,
    ReviewRelationshipRequest,
)
from ecowatch.modules.intelligence.service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/entities", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
def create_entity(
    payload: CreateEntityRequest,
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> EntityResponse:
    """Record an environmental entity with its declared coordinate reference system."""
    record = IntelligenceService(db).create_environmental_entity(
        principal, **payload.model_dump(), requestId=requestId
    )
    return EntityResponse.model_validate(record)


@router.post(
    "/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED
)
def propose_relationship(
    payload: ProposeRelationshipRequest,
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> RelationshipResponse:
    """Propose an evidence-backed relationship with explicit uncertainty and alternatives."""
    record = IntelligenceService(db).propose_environmental_relationship(
        principal, **payload.model_dump(), requestId=requestId
    )
    return RelationshipResponse.model_validate(record)


@router.post("/relationships/{relationshipId}/review", response_model=RelationshipResponse)
def review_relationship(
    payload: ReviewRelationshipRequest,
    relationshipId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_REVIEW)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> RelationshipResponse:
    """Record a human review decision on one proposed relationship."""
    record = IntelligenceService(db).review_environmental_relationship(
        principal, relationshipId=relationshipId, **payload.model_dump(), requestId=requestId
    )
    return RelationshipResponse.model_validate(record)


@router.post("/analyses", response_model=AnalysisRunResponse, status_code=status.HTTP_202_ACCEPTED)
def queue_analysis(
    payload: QueueAnalysisRequest,
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AnalysisRunResponse:
    """Queue a reproducible analysis run; 202 keeps inference out of the request."""
    record = IntelligenceService(db).queue_analysis_run(
        principal, **payload.model_dump(), requestId=requestId
    )
    return AnalysisRunResponse.model_validate(record)


@router.post(
    "/analyses/{analysisRunId}/outputs",
    response_model=AnalysisOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_analysis_output(
    payload: RecordAnalysisOutputRequest,
    analysisRunId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AnalysisOutputResponse:
    """Attach a derived output to a running or succeeded analysis run."""
    record = IntelligenceService(db).record_analysis_output(
        principal, analysisRunId=analysisRunId, **payload.model_dump(), requestId=requestId
    )
    return AnalysisOutputResponse.model_validate(record)


@router.post("/predictions/check", response_model=PredictionCheckResponse)
def check_prediction_gate(
    payload: PredictionCheckRequest,
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
) -> PredictionCheckResponse:
    """Check prediction release preconditions; no prediction is produced here."""
    IntelligenceService(db).request_prediction(principal, **payload.model_dump())
    return PredictionCheckResponse(allowed=True)


@router.get("/entities", response_model=CursorPage[EntityResponse])
def list_entities(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[EntityResponse]:
    """List environmental entities visible within the caller's organisations."""
    return IntelligenceService(db).list_entities(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get("/relationships", response_model=CursorPage[RelationshipResponse])
def list_relationships(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[RelationshipResponse]:
    """List relationships with their recorded review state (decision support only)."""
    return IntelligenceService(db).list_relationships(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get("/analyses", response_model=CursorPage[AnalysisRunResponse])
def list_analysis_runs(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[AnalysisRunResponse]:
    """List analysis runs; status is a processing state, not an environmental finding."""
    return IntelligenceService(db).list_analysis_runs(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get(
    "/analyses/{analysisRunId}/outputs", response_model=CursorPage[AnalysisOutputResponse]
)
def list_analysis_outputs(
    analysisRunId: uuid.UUID = Path(),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.INTELLIGENCE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[AnalysisOutputResponse]:
    """List derived outputs of one in-scope analysis run, awaiting human interpretation."""
    return IntelligenceService(db).list_analysis_outputs(
        principal, analysisRunId, cursor=cursor, limit=limit
    )
