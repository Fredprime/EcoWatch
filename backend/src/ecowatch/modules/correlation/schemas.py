"""Pydantic boundary schemas for evidence correlation."""

import uuid
from datetime import datetime

from pydantic import Field

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.correlation.models import RelationshipStatus


class CorrelationSuggestionResponse(CamelModel):
    """A pairwise suggestion with its reasons and reviewer decision state."""

    id: uuid.UUID
    organisationId: uuid.UUID
    observationAId: uuid.UUID
    observationBId: uuid.UUID
    task: str
    score: float
    components: dict[str, float]
    missingSignals: list[str]
    reasons: list[str]
    sourceIndependent: bool
    ambiguous: bool = False
    status: str
    methodVersion: str
    decidedByUserId: uuid.UUID | None = None
    decidedAt: datetime | None = None
    decisionReason: str | None = None
    createdAt: datetime


class CorrelationDecisionRequest(CamelModel):
    """A reviewer's decision on one suggestion. `suggested` is not a decision."""

    decision: RelationshipStatus
    reason: str | None = Field(default=None, max_length=2000)


class CorrelationClusterResponse(CamelModel):
    """A provisional cluster. Not a case, and it has no case field to promote."""

    id: uuid.UUID
    organisationId: uuid.UUID
    observationIds: list[uuid.UUID]
    createdAt: datetime


class CorrelationReopenRequest(CamelModel):
    """Reopening a decision. The reason is required: an unexplained reversal is
    an edit by another name."""

    reason: str = Field(min_length=1, max_length=2000)


class CorrelationScanResponse(CamelModel):
    """Identifier of the queued scan, so the caller can poll instead of waiting."""

    observationId: uuid.UUID
    jobId: uuid.UUID
