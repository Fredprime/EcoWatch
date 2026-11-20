"""Service layer for governed controlled-vocabulary configuration."""

import uuid

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.identity.permissions import Principal
from ecowatch.modules.vocabularies.models import VocabularyTerm
from ecowatch.modules.vocabularies.repository import VocabularyTermRepository
from ecowatch.modules.vocabularies.schemas import (
    CreateVocabularyTermRequest,
    UpdateVocabularyTermRequest,
    VocabularyTermResponse,
)


class VocabularyService:
    """System-admin-only term governance; never classifies or finds anything."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = VocabularyTermRepository(session)

    @staticmethod
    def _require_system_admin(principal: Principal) -> None:
        if not principal.is_system_admin:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Only system_admin may manage controlled vocabularies",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

    def _get_term(self, termId: uuid.UUID) -> VocabularyTerm:
        term = self._repo.get_by_id(termId)
        if term is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Vocabulary term not found.",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="termId",
            )
        return term

    def _audit(
        self,
        principal: Principal,
        action: str,
        term: VocabularyTerm,
        requestId: str | None,
    ) -> None:
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action=action,
            targetType="vocabularyTerm",
            targetId=term.id,
            details={"vocabularyKey": term.vocabularyKey, "code": term.code},
            requestId=requestId,
        )

    def create_term(
        self,
        principal: Principal,
        payload: CreateVocabularyTermRequest,
        *,
        requestId: str | None = None,
    ) -> VocabularyTerm:
        """Create a governed term, rejecting a duplicate key/code pair."""
        self._require_system_admin(principal)
        if self._repo.get_by_key_and_code(payload.vocabularyKey, payload.code) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A term with this code already exists in the vocabulary.",
                statusCode=status.HTTP_409_CONFLICT,
                field="code",
            )
        term = self._repo.create(
            vocabularyKey=payload.vocabularyKey,
            code=payload.code,
            label=payload.label,
            description=payload.description,
        )
        self._audit(principal, "vocabulary.term.created", term, requestId)
        self._session.commit()
        self._session.refresh(term)
        return term

    def list_terms(
        self,
        principal: Principal,
        *,
        vocabularyKey: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[VocabularyTermResponse]:
        """List terms newest-first, optionally scoped to one vocabulary key."""
        self._require_system_admin(principal)
        rows, nextCursor, hasMore = self._repo.list_terms(
            vocabularyKey=vocabularyKey, cursor=cursor, limit=limit
        )
        return CursorPage[VocabularyTermResponse](
            items=[VocabularyTermResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def update_term(
        self,
        principal: Principal,
        termId: uuid.UUID,
        payload: UpdateVocabularyTermRequest,
        *,
        requestId: str | None = None,
    ) -> VocabularyTerm:
        """Update label, description, or active state (including reactivation)."""
        self._require_system_admin(principal)
        term = self._get_term(termId)
        if payload.label is not None:
            term.label = payload.label
        if payload.description is not None:
            term.description = payload.description
        if payload.isActive is not None:
            term.isActive = payload.isActive
        self._audit(principal, "vocabulary.term.updated", term, requestId)
        self._session.commit()
        self._session.refresh(term)
        return term

    def deactivate_term(
        self,
        principal: Principal,
        termId: uuid.UUID,
        *,
        requestId: str | None = None,
    ) -> VocabularyTerm:
        """Deactivate a term without deleting governed configuration history."""
        self._require_system_admin(principal)
        term = self._get_term(termId)
        term.isActive = False
        self._audit(principal, "vocabulary.term.deactivated", term, requestId)
        self._session.commit()
        self._session.refresh(term)
        return term
