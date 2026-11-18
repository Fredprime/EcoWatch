"""FastAPI router for evidence correlation suggestions and reviewer decisions."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.modules.correlation.schemas import (
    CorrelationDecisionRequest,
    CorrelationReopenRequest,
    CorrelationScanResponse,
    CorrelationSuggestionResponse,
)
from ecowatch.modules.correlation.service import CorrelationService
from ecowatch.modules.identity.permissions import Permission, Principal

router = APIRouter(prefix="/correlation", tags=["correlation"])


@router.get("/suggestions", response_model=list[CorrelationSuggestionResponse])
def list_suggestions(
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.CORRELATION_READ)),
    db: Session = Depends(get_db),
) -> list[CorrelationSuggestionResponse]:
    """Return open suggestions for the caller's organisations, best first."""
    rows = CorrelationService(db).list_suggestions(principal, limit=limit)
    return [CorrelationSuggestionResponse.model_validate(row) for row in rows]


@router.post(
    "/observations/{observationId}/scan",
    response_model=CorrelationScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def scan_observation(
    observationId: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.CORRELATION_REVIEW)),
    db: Session = Depends(get_db),
) -> CorrelationScanResponse:
    """Queue a correlation scan for one observation.

    Returns 202 with a job id: scoring never runs inside this request, so intake
    latency stays independent of model work (`NFR-001`).
    """
    jobId = CorrelationService(db).request_scan(principal, observationId)
    return CorrelationScanResponse(observationId=observationId, jobId=jobId)


@router.post(
    "/suggestions/{relationshipId}/decision",
    response_model=CorrelationSuggestionResponse,
)
def decide_suggestion(
    relationshipId: uuid.UUID,
    payload: CorrelationDecisionRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.CORRELATION_REVIEW)),
    db: Session = Depends(get_db),
) -> CorrelationSuggestionResponse:
    """Record accept, reject, or ambiguous on one suggestion, with an audit event."""
    relationship = CorrelationService(db).decide(
        principal,
        relationshipId,
        payload.decision,
        reason=payload.reason,
        requestId=get_request_id(request),
    )
    return CorrelationSuggestionResponse.model_validate(relationship)


@router.post(
    "/suggestions/{relationshipId}/reopen",
    response_model=CorrelationSuggestionResponse,
)
def reopen_suggestion(
    relationshipId: uuid.UUID,
    payload: CorrelationReopenRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.CORRELATION_REVIEW)),
    db: Session = Depends(get_db),
) -> CorrelationSuggestionResponse:
    """Return a decided suggestion to the queue, with the reason audited."""
    relationship = CorrelationService(db).reopen(
        principal,
        relationshipId,
        reason=payload.reason,
        requestId=get_request_id(request),
    )
    return CorrelationSuggestionResponse.model_validate(relationship)
