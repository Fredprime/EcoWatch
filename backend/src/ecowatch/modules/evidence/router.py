"""FastAPI routes for evidence upload, scan status, and restricted retrieval."""

import uuid
from collections.abc import Iterator

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    Path,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import (
    get_optional_principal,
    get_request_id,
    get_storage,
    require_permission,
)
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.evidence.schemas import (
    EvidenceAssetResponse,
    EvidenceScanStatusResponse,
)
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.observations.models import AccessClass

router = APIRouter(tags=["evidence"])


def _iter_chunks(data: bytes, chunkSize: int = 65_536) -> Iterator[bytes]:
    for offset in range(0, len(data), chunkSize):
        yield data[offset : offset + chunkSize]


@router.post(
    "/observations/{observationId}/evidence",
    response_model=EvidenceAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    observationId: uuid.UUID = Path(),
    file: UploadFile = File(...),
    accessClass: AccessClass = Form(default=AccessClass.RESTRICTED),
    trackingCode: str | None = Header(default=None, alias="X-Tracking-Code"),
    idempotencyKey: uuid.UUID | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(get_optional_principal),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
    settings: Settings = Depends(get_settings),
    requestId: str | None = Depends(get_request_id),
) -> EvidenceAssetResponse:
    """Upload evidence for an observation via RBAC or matching X-Tracking-Code."""
    rawBytes = await file.read(settings.maxUploadBytes + 1)
    return EvidenceService(db, storage).upload_evidence(
        principal,
        observationId,
        rawBytes=rawBytes,
        filename=file.filename,
        declaredMimeType=file.content_type,
        accessClass=accessClass,
        trackingCode=trackingCode,
        idempotencyKey=idempotencyKey,
        settings=settings,
        requestId=requestId,
    )


@router.get(
    "/observations/{observationId}/evidence",
    response_model=list[EvidenceAssetResponse],
)
def list_observation_evidence(
    observationId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.EVIDENCE_READ_DERIVATIVE)),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
) -> list[EvidenceAssetResponse]:
    """List evidence assets and derivatives for an org-scoped observation."""
    return EvidenceService(db, storage).list_observation_evidence(principal, observationId)


@router.get("/evidence/{assetId}/original")
def download_original_evidence(
    assetId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.EVIDENCE_READ_ORIGINAL)),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
    requestId: str | None = Depends(get_request_id),
) -> StreamingResponse:
    """Stream untouched original evidence bytes with audit logging and scan checks."""
    asset, data = EvidenceService(db, storage).get_original_bytes(
        principal, assetId, requestId=requestId
    )
    return StreamingResponse(
        _iter_chunks(data),
        media_type=asset.detectedMimeType,
        headers={
            "Content-Disposition": f'attachment; filename="{asset.originalFilename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/evidence/{assetId}/derivatives/{derivativeId}")
def download_evidence_derivative(
    assetId: uuid.UUID = Path(),
    derivativeId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.EVIDENCE_READ_DERIVATIVE)),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
) -> Response:
    """Serve an EXIF-stripped derivative preview or thumbnail."""
    derivative, data = EvidenceService(db, storage).get_derivative_bytes(
        principal, assetId, derivativeId
    )
    return Response(
        content=data,
        media_type=derivative.mimeType,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/evidence/{assetId}/scan-status", response_model=EvidenceScanStatusResponse)
def get_evidence_scan_status(
    assetId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.EVIDENCE_READ_SCAN_STATUS)),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
) -> EvidenceScanStatusResponse:
    """Inspect scan status and extracted metadata for an org-scoped evidence asset."""
    return EvidenceService(db, storage).get_scan_status(principal, assetId)
