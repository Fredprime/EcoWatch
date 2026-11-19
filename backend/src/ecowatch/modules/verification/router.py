"""FastAPI routes for qualified measurements, verification gates, and publications."""

import uuid

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
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
