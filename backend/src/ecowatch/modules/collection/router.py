"""FastAPI routes for observation intake and anonymous receipt lookup."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_optional_principal, get_request_id
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.modules.collection.schemas import (
    CreateObservationRequest,
    IntakeReceiptResponse,
    ReceiptLookupRequest,
    ReceiptLookupResponse,
)
from ecowatch.modules.collection.service import CollectionService
from ecowatch.modules.identity.permissions import Principal

router = APIRouter(tags=["collection"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client and request.client.host else "unknown"


@router.post(
    "/observations",
    response_model=IntakeReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_observation(
    payload: CreateObservationRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(get_optional_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    requestId: str | None = Depends(get_request_id),
) -> IntakeReceiptResponse:
    """Idempotent intake endpoint accepting anonymous and authenticated observations."""
    receipt, isReplay = CollectionService(db).submit_observation(
        principal,
        payload,
        settings=settings,
        clientIp=_client_ip(request),
        requestId=requestId,
    )
    response.status_code = status.HTTP_200_OK if isReplay else status.HTTP_201_CREATED
    return receipt


@router.post(
    "/observations/receipt-lookup",
    response_model=ReceiptLookupResponse,
    status_code=status.HTTP_200_OK,
)
def lookup_receipt(
    payload: ReceiptLookupRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReceiptLookupResponse:
    """Throttled anonymous receipt lookup by high-entropy tracking code."""
    return CollectionService(db).lookup_receipt(
        payload,
        settings=settings,
        clientIp=_client_ip(request),
    )
