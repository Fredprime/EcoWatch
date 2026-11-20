"""Repository for governed controlled-vocabulary term records."""

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.vocabularies.models import VocabularyTerm


class VocabularyTermRepository:
    """Create, look up, and cursor-page controlled-vocabulary terms."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, termId: uuid.UUID) -> VocabularyTerm | None:
        """Return a term by primary key, or None."""
        return self._session.get(VocabularyTerm, termId)

    def get_by_key_and_code(self, vocabularyKey: str, code: str) -> VocabularyTerm | None:
        """Return an existing term for a key/code pair, or None."""
        return self._session.scalar(
            sa.select(VocabularyTerm).where(
                VocabularyTerm.vocabularyKey == vocabularyKey,
                VocabularyTerm.code == code,
            )
        )

    def create(
        self,
        *,
        vocabularyKey: str,
        code: str,
        label: str,
        description: str | None,
    ) -> VocabularyTerm:
        """Persist a new term inside the caller's transaction."""
        term = VocabularyTerm(
            vocabularyKey=vocabularyKey,
            code=code,
            label=label,
            description=description,
            isActive=True,
        )
        self._session.add(term)
        self._session.flush()
        return term

    def list_terms(
        self,
        *,
        vocabularyKey: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[VocabularyTerm], str | None, bool]:
        """Return a newest-first cursor page, optionally filtered to one key."""
        stmt = sa.select(VocabularyTerm)
        if vocabularyKey is not None:
            stmt = stmt.where(VocabularyTerm.vocabularyKey == vocabularyKey)
        return paginate_descending(
            self._session,
            stmt,
            timeCol=VocabularyTerm.createdAt,
            idCol=VocabularyTerm.id,
            cursor=cursor,
            limit=limit,
        )
