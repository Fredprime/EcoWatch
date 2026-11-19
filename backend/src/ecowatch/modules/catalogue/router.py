"""FastAPI routes for the environmental dataset catalogue."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.catalogue.schemas import (
    AddDatasetVersionRequest,
    CreateDatasetRequest,
    DatasetResponse,
    DatasetVersionResponse,
)
from ecowatch.modules.catalogue.service import CatalogueService
from ecowatch.modules.identity.permissions import Permission, Principal

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


@router.post("/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: CreateDatasetRequest,
    principal: Principal = Depends(require_permission(Permission.CATALOGUE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> DatasetResponse:
    """Create a rights-recorded dataset after catalogue write permission checks."""
    record = CatalogueService(db).create_dataset(
        principal, **payload.model_dump(), requestId=requestId
    )
    return DatasetResponse.model_validate(record)


@router.post(
    "/datasets/{datasetId}/versions",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_dataset_version(
    payload: AddDatasetVersionRequest,
    datasetId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.CATALOGUE_WRITE)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> DatasetVersionResponse:
    """Append a complete provenance snapshot to an in-scope dataset."""
    record = CatalogueService(db).add_dataset_version(
        principal, datasetId=datasetId, **payload.model_dump(), requestId=requestId
    )
    return DatasetVersionResponse.model_validate(record)


@router.get("/datasets", response_model=CursorPage[DatasetResponse])
def list_datasets(
    organisationId: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.CATALOGUE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[DatasetResponse]:
    """List datasets recorded with their licence, attribution and permitted use."""
    return CatalogueService(db).list_datasets(
        principal, organisationId=organisationId, cursor=cursor, limit=limit
    )


@router.get(
    "/datasets/{datasetId}/versions", response_model=CursorPage[DatasetVersionResponse]
)
def list_dataset_versions(
    datasetId: uuid.UUID = Path(),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.CATALOGUE_WRITE)),
    db: Session = Depends(get_db),
) -> CursorPage[DatasetVersionResponse]:
    """List the immutable provenance snapshots of one in-scope dataset."""
    return CatalogueService(db).list_dataset_versions(
        principal, datasetId, cursor=cursor, limit=limit
    )
