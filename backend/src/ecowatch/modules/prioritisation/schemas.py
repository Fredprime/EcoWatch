"""Pydantic boundary schemas for evidence-honest prioritisation."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.phase3Contracts import clean_required_text as _required
from ecowatch.modules.prioritisation.enums import PriorityDecision


class CreateAssessmentRequest(CamelModel):
    """Transparent prioritisation factors; missing inputs are never imputed."""

    organisationId: uuid.UUID
    caseId: uuid.UUID
    methodName: str = Field(min_length=1, max_length=200)
    methodVersion: str = Field(min_length=1, max_length=100)
    factors: dict[str, Any] = Field(default_factory=dict)
    assessmentAt: datetime | None = None
    compositeRank: float | None = Field(default=None, ge=0, le=1000000)
    rankingMethodRef: str | None = Field(default=None, max_length=10000)
    rankIsNotSeverity: bool | None = None

    @field_validator("methodName", "methodVersion")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class RecordDecisionRequest(CamelModel):
    """Accountable human decision with a recorded rationale."""

    organisationId: uuid.UUID
    decision: PriorityDecision
    rationale: str = Field(min_length=1, max_length=10000)

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _required(value)


class AssessmentResponse(CamelModel):
    """Prioritisation assessment exposing factors, gaps, and human decision."""

    id: uuid.UUID
    organisationId: uuid.UUID
    caseId: uuid.UUID
    assessmentAt: datetime
    methodName: str
    methodVersion: str
    factors: dict[str, Any]
    missingInputs: list[str]
    compositeRank: float | None = None
    rankingMethodRef: str | None = None
    rankIsNotSeverity: bool | None = None
    decision: str | None = None
    decisionRationale: str | None = None
    decidedByUserId: uuid.UUID | None = None
    decidedAt: datetime | None = None
    reviewerUserId: uuid.UUID | None = None
    reviewedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime
