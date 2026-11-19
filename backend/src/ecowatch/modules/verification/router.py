"""FastAPI routes for qualified measurements, verification gates, and publications."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.verification.schemas import (
    AssessmentResponse,
    CreateAssessmentRequest,
    CreateIndicatorRequest,
    FinaliseAssessmentRequest,
    IndicatorResponse,
    MeasurementResponse,
    PublicationResponse,
    PublishSummaryRequest,
    RecordMeasurementRequest,
    RecoveryVerificationRequest,
    RetractPublicationRequest,
)
from ecowatch.modules.verification.service import VerificationService

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/indicators", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
def create_indicator(
    payload: CreateIndicatorRequest,
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_APPROVE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> IndicatorResponse:
    """Create an approved indicator definition with documented criteria."""
    record = VerificationService(db).create_indicator_definition(
        principal, **payload.model_dump(), requestId=requestId
    )
    return IndicatorResponse.model_validate(record)


@router.post(
    "/measurements/{indicatorDefinitionId}",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_measurement(
    payload: RecordMeasurementRequest,
    indicatorDefinitionId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> MeasurementResponse:
    """Record a qualified measurement without inventing a censored value."""
    record = VerificationService(db).record_measurement(
        principal,
        indicatorDefinitionId=indicatorDefinitionId,
        **payload.model_dump(),
        requestId=requestId,
    )
    return MeasurementResponse.model_validate(record)


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: CreateAssessmentRequest,
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AssessmentResponse:
    """Record an observed-change conclusion; recovery is a separate gated path."""
    record = VerificationService(db).create_assessment(
        principal, **payload.model_dump(), requestId=requestId
    )
    return AssessmentResponse.model_validate(record)


@router.post("/assessments/{assessmentId}/finalise", response_model=AssessmentResponse)
def finalise_assessment(
    payload: FinaliseAssessmentRequest,
    assessmentId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_APPROVE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AssessmentResponse:
    """Finalise a draft assessment with documented criteria."""
    record = VerificationService(db).finalise_assessment(
        principal, assessmentId=assessmentId, **payload.model_dump(), requestId=requestId
    )
    return AssessmentResponse.model_validate(record)


@router.post("/assessments/{assessmentId}/recovery", response_model=AssessmentResponse)
def verify_recovery(
    payload: RecoveryVerificationRequest,
    assessmentId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_APPROVE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> AssessmentResponse:
    """Run the dedicated recovery gate; specialists only, with approved criteria."""
    record = VerificationService(db).verify_recovery(
        principal, assessmentId=assessmentId, **payload.model_dump(), requestId=requestId
    )
    return AssessmentResponse.model_validate(record)


@router.post(
    "/publications", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED
)
def publish_summary(
    payload: PublishSummaryRequest,
    principal: Principal = Depends(require_permission(Permission.PUBLICATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> PublicationResponse:
    """Store the exact approved public text with its approver and role."""
    record = VerificationService(db).publish_summary(
        principal, **payload.model_dump(), requestId=requestId
    )
    return PublicationResponse.model_validate(record)


@router.post("/publications/{publicationId}/retract", response_model=PublicationResponse)
def retract_publication(
    payload: RetractPublicationRequest,
    publicationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.PUBLICATION_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> PublicationResponse:
    """Retract a publication as an audited event rather than editing its text."""
    record = VerificationService(db).retract_publication(
        principal, publicationId=publicationId, **payload.model_dump(), requestId=requestId
    )
    return PublicationResponse.model_validate(record)


@router.get("/indicators", response_model=CursorPage[IndicatorResponse])
def list_indicators(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[IndicatorResponse]:
    """List approved indicator definitions within the caller's organisations."""
    return VerificationService(db).list_indicators(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get("/measurements", response_model=CursorPage[MeasurementResponse])
def list_measurements(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[MeasurementResponse]:
    """List qualified measurements within the caller's organisations."""
    return VerificationService(db).list_measurements(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get("/assessments", response_model=CursorPage[AssessmentResponse])
def list_assessments(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[AssessmentResponse]:
    """List outcome assessments within the caller's organisations."""
    return VerificationService(db).list_assessments(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get("/publications", response_model=CursorPage[PublicationResponse])
def list_publications(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.VERIFICATION_READ)),
    db: Session = Depends(get_db),
) -> CursorPage[PublicationResponse]:
    """List approved public text records with their retraction state."""
    return VerificationService(db).list_publications(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )
