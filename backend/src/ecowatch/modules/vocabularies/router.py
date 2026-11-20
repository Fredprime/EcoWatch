"""FastAPI routes for governed controlled vocabularies (system_admin only)."""

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from ecowatch.api.dependencies import get_request_id, require_permission
from ecowatch.core.database import get_db
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.vocabularies.schemas import (
    CreateVocabularyTermRequest,
    UpdateVocabularyTermRequest,
    VocabularyTermResponse,
)
from ecowatch.modules.vocabularies.service import VocabularyService

router = APIRouter(prefix="/vocabularies", tags=["vocabularies"])


@router.post("/terms", response_model=VocabularyTermResponse, status_code=status.HTTP_201_CREATED)
def create_vocabulary_term(
    payload: CreateVocabularyTermRequest,
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> VocabularyTermResponse:
    """Create a governed vocabulary term (system_admin only)."""
    term = VocabularyService(db).create_term(principal, payload, requestId=requestId)
    return VocabularyTermResponse.model_validate(term)


@router.get("/terms", response_model=CursorPage[VocabularyTermResponse])
def list_vocabulary_terms(
    vocabularyKey: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
) -> CursorPage[VocabularyTermResponse]:
    """List governed vocabulary terms, optionally filtered by key (system_admin only)."""
    return VocabularyService(db).list_terms(
        principal, vocabularyKey=vocabularyKey, cursor=cursor, limit=limit
    )


@router.patch("/terms/{termId}", response_model=VocabularyTermResponse)
def update_vocabulary_term(
    payload: UpdateVocabularyTermRequest,
    termId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> VocabularyTermResponse:
    """Update a term's presentation or active state (system_admin only)."""
    term = VocabularyService(db).update_term(principal, termId, payload, requestId=requestId)
    return VocabularyTermResponse.model_validate(term)


@router.post("/terms/{termId}/deactivate", response_model=VocabularyTermResponse)
def deactivate_vocabulary_term(
    termId: uuid.UUID = Path(),
    principal: Principal = Depends(require_permission(Permission.ADMIN_MANAGE_SYSTEM)),
    db: Session = Depends(get_db),
    requestId: str | None = Depends(get_request_id),
) -> VocabularyTermResponse:
    """Deactivate a governed term without deleting it (system_admin only)."""
    term = VocabularyService(db).deactivate_term(principal, termId, requestId=requestId)
    return VocabularyTermResponse.model_validate(term)
