"""Pydantic boundary schemas for controlled-vocabulary configuration."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, field_validator, model_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.phase3Contracts import clean_required_text as _required

_CODE_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*$"


class CreateVocabularyTermRequest(CamelModel):
    """Create one term under a controlled-vocabulary key."""

    vocabularyKey: str = Field(min_length=1, max_length=100, pattern=_CODE_PATTERN)
    code: str = Field(min_length=1, max_length=100, pattern=_CODE_PATTERN)
    label: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("vocabularyKey", "code", "label")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class UpdateVocabularyTermRequest(CamelModel):
    """Change a term's presentation or active state; activation is an update."""

    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    isActive: bool | None = None

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        return _required(value) if value is not None else None

    @model_validator(mode="after")
    def require_a_change(self) -> UpdateVocabularyTermRequest:
        if all(value is None for value in (self.label, self.description, self.isActive)):
            raise ValueError("At least one field must be provided")
        return self


class VocabularyTermResponse(CamelModel):
    """Governed vocabulary term as returned to system administrators."""

    id: uuid.UUID
    vocabularyKey: str
    code: str
    label: str
    description: str | None = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
