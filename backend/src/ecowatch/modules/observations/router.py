"""FastAPI routes for observations, versions, quality flags, sources, methods, and units."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import (
    get_current_principal,
    get_request_id,
    rate_limit_dependency,
    require_permission,
)
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.observations.schemas import (
    CreateCorrectionRequest,
    CreateMethodRequest,
    CreateUnitRequest,
    HideObservationRequest,
    MethodResponse,
    ObservationExportResponse,
    ObservationPublicSummaryResponse,
    ObservationRestrictedResponse,
    ObservationSourceResponse,
    ObservationVersionResponse,
    UnitResponse,
    UpdateQualityFlagsRequest,
)
from ecowatch.modules.observations.service import ObservationService

router = APIRouter(tags=["observations"])


@router.get("/observations", response_model=CursorPage[ObservationPublicSummaryResponse])
def list_observations(
    organisationId: uuid.UUID | None = Query(default=None),
    observationType: str | None = Query(default=None),
    sourceType: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CursorPage[ObservationPublicSummaryResponse]:
    """List redacted observations scoped to accessible organisations or own submissions."""
    return ObservationService(db).list_observations(
        principal,
        organisationId=organisationId,
        observationType=observationType,
        sourceType=sourceType,
        cursor=cursor,
        limit=limit,
    )


@router.get(
    "/observations/export",
    response_model=ObservationExportResponse,
    dependencies=[
        Depends(
            rate_limit_dependency(
                "obs_export",
                "expensiveEndpointRateLimit",
                "expensiveEndpointWindowSeconds",
            )
        )
    ],
)
def export_observations(
    organisationId: uuid.UUID = Query(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> ObservationExportResponse:
    """Export an organisation's observations with history and source records (OA own org / SA)."""
    return ObservationService(db).export_observations(
        principal, organisationId, requestId=requestId
    )


@router.get(
    "/observations/{observationId}",
    response_model=ObservationRestrictedResponse | ObservationPublicSummaryResponse,
)
def get_observation(
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ObservationRestrictedResponse | ObservationPublicSummaryResponse:
    """Return org-scoped observation details (404 on cross-organisation access)."""
    return ObservationService(db).get_observation(principal, observationId)


@router.get(
    "/observations/{observationId}/versions",
    response_model=list[ObservationVersionResponse],
)
def list_observation_versions(
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.OBS_READ_REDACTED)),
    db: Session = Depends(get_db),
) -> list[ObservationVersionResponse]:
    """Return append-only version history for an org-scoped observation."""
    return ObservationService(db).list_versions(principal, observationId)


@router.post(
    "/observations/{observationId}/corrections",
    response_model=ObservationRestrictedResponse,
    status_code=status.HTTP_201_CREATED,
)
def correct_observation(
    payload: CreateCorrectionRequest,
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.OBS_CORRECT)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    requestId: str | None = Depends(get_request_id),
) -> ObservationRestrictedResponse:
    """Append an observation correction version without mutating prior history."""
    return ObservationService(db).correct_observation(
        principal,
        observationId,
        payload,
        settings=settings,
        requestId=requestId,
    )


@router.patch(
    "/observations/{observationId}/quality-flags",
    response_model=ObservationPublicSummaryResponse,
)
def update_quality_flags(
    payload: UpdateQualityFlagsRequest,
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.OBS_QUALITY_FLAG)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> ObservationPublicSummaryResponse:
    """Update observation quality flags (RV/ES/SA, org-scoped)."""
    return ObservationService(db).update_quality_flags(
        principal,
        observationId,
        payload,
        requestId=requestId,
    )


@router.get(
    "/observations/{observationId}/source",
    response_model=ObservationSourceResponse,
)
def get_observation_source(
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.SOURCE_READ)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> ObservationSourceResponse:
    """Read isolated contributor identity/contact (OA own org / SA only) with audit event."""
    return ObservationService(db).get_source(principal, observationId, requestId=requestId)


@router.post(
    "/observations/{observationId}/hide",
    response_model=ObservationRestrictedResponse,
)
def hide_observation(
    payload: HideObservationRequest,
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> ObservationRestrictedResponse:
    """Tombstone an observation (SA only): hide from all views, clear source PII, audit."""
    return ObservationService(db).hide_observation(
        principal, observationId, payload, requestId=requestId
    )


@router.get("/methods", response_model=CursorPage[MethodResponse])
def list_methods(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CursorPage[MethodResponse]:
    """List registered measurement/field methods."""
    return ObservationService(db).list_methods(cursor=cursor, limit=limit)


@router.post("/methods", response_model=MethodResponse, status_code=status.HTTP_201_CREATED)
def create_method(
    payload: CreateMethodRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> MethodResponse:
    """Create a field or laboratory method definition (ES/SA only)."""
    return ObservationService(db).create_method(principal, payload, requestId=requestId)


@router.get("/units", response_model=CursorPage[UnitResponse])
def list_units(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CursorPage[UnitResponse]:
    """List controlled measurement units."""
    return ObservationService(db).list_units(cursor=cursor, limit=limit)


@router.post("/units", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: CreateUnitRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> UnitResponse:
    """Register a controlled measurement unit (ES/SA only)."""
    return ObservationService(db).create_unit(principal, payload, requestId=requestId)
