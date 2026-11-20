"""Pydantic boundary schemas for environmental intelligence records."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.core.spatial import validate_wkt_geometry
from ecowatch.modules.intelligence.enums import (
    AnalysisOutputType,
    AnalysisType,
    EnvironmentalEntityType,
    EnvironmentalRelationshipType,
    ReviewState,
    UncertaintyLevel,
)
from ecowatch.modules.phase3Contracts import clean_required_text as _required
from ecowatch.modules.phase3Contracts import geometry_text as _geometry_text


class CreateEntityRequest(CamelModel):
    """Payload for recording an environmental entity or monitored asset."""

    organisationId: uuid.UUID
    entityType: EnvironmentalEntityType
    name: str = Field(min_length=1, max_length=200)
    crs: str = Field(default="EPSG:4326", min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=10000)
    geometry: str | None = Field(default=None, max_length=50000)
    parentEntityId: uuid.UUID | None = None

    @field_validator("name", "crs")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)

    @field_validator("geometry", mode="before")
    @classmethod
    def validate_geometry(cls, value: Any) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return validate_wkt_geometry(str(value))


class ProposeRelationshipRequest(CamelModel):
    """Evidence-backed, explicitly uncertain proposed relationship."""

    organisationId: uuid.UUID
    relationshipType: EnvironmentalRelationshipType
    evidenceSummary: str = Field(min_length=1, max_length=10000)
    uncertainty: UncertaintyLevel
    uncertaintyNote: str = Field(min_length=1, max_length=10000)
    alternativeExplanations: str = Field(min_length=1, max_length=10000)
    methodName: str = Field(min_length=1, max_length=200)
    methodVersion: str = Field(min_length=1, max_length=100)
    reviewState: ReviewState = ReviewState.PROPOSED
    fromEntityId: uuid.UUID | None = None
    fromObservationId: uuid.UUID | None = None
    toEntityId: uuid.UUID | None = None
    toObservationId: uuid.UUID | None = None
    spatialScope: str | None = Field(default=None, max_length=10000)
    temporalStartAt: datetime | None = None
    temporalEndAt: datetime | None = None
    supportingEvidenceAssetIds: list[str] = Field(default_factory=list, max_length=200)

    @field_validator(
        "evidenceSummary",
        "uncertaintyNote",
        "alternativeExplanations",
        "methodName",
        "methodVersion",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class ReviewRelationshipRequest(CamelModel):
    """Human review decision on a proposed environmental relationship."""

    organisationId: uuid.UUID
    reviewState: ReviewState


class QueueAnalysisRequest(CamelModel):
    """Reproducible analysis run request with full input and method provenance."""

    organisationId: uuid.UUID
    question: str = Field(min_length=1, max_length=10000)
    analysisType: AnalysisType
    methodName: str = Field(min_length=1, max_length=200)
    methodVersion: str = Field(min_length=1, max_length=100)
    inputDatasetVersionIds: list[str] = Field(min_length=1, max_length=200)
    crs: str = Field(min_length=1, max_length=50)
    parameters: dict[str, Any] = Field(default_factory=dict)
    limitations: str = Field(min_length=1, max_length=10000)
    caseId: uuid.UUID | None = None
    qualityMaskNotes: str | None = Field(default=None, max_length=10000)
    seasonalContext: str | None = Field(default=None, max_length=10000)

    @field_validator("question", "methodName", "methodVersion", "crs", "limitations")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class RecordAnalysisOutputRequest(CamelModel):
    """Derived output record for a running or succeeded analysis run."""

    organisationId: uuid.UUID
    outputType: AnalysisOutputType
    summary: str = Field(min_length=1, max_length=10000)
    limitations: str = Field(min_length=1, max_length=10000)
    storageKey: str | None = Field(default=None, max_length=500)
    derivedFromObservationIds: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("summary", "limitations")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class PredictionCheckRequest(CamelModel):
    """Preconditions for releasing a predictive feature; never a prediction itself."""

    organisationId: uuid.UUID
    modelName: str | None = Field(default=None, max_length=200)
    modelVersion: str | None = Field(default=None, max_length=100)
    validationReportRef: str | None = Field(default=None, max_length=500)
    representativeDataRef: str | None = Field(default=None, max_length=500)
    targetDefined: bool = False


class PredictionCheckResponse(CamelModel):
    """Confirmation that the prediction release gate passed; no result is produced."""

    allowed: bool


class EntityResponse(CamelModel):
    """Staff view of an environmental entity."""

    id: uuid.UUID
    organisationId: uuid.UUID
    entityType: str
    name: str
    description: str | None = None
    geometry: str | None = None
    crs: str
    parentEntityId: uuid.UUID | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_validator("geometry", mode="before")
    @classmethod
    def serialize_geometry(cls, value: Any) -> str | None:
        return _geometry_text(value)


class RelationshipResponse(CamelModel):
    """Staff view of an environmental relationship with review state."""

    id: uuid.UUID
    organisationId: uuid.UUID
    relationshipType: str
    fromEntityId: uuid.UUID | None = None
    fromObservationId: uuid.UUID | None = None
    toEntityId: uuid.UUID | None = None
    toObservationId: uuid.UUID | None = None
    spatialScope: str | None = None
    temporalStartAt: datetime | None = None
    temporalEndAt: datetime | None = None
    evidenceSummary: str
    supportingEvidenceAssetIds: list[str]
    methodName: str
    methodVersion: str
    uncertainty: str
    uncertaintyNote: str
    alternativeExplanations: str
    reviewState: str
    reviewedByUserId: uuid.UUID | None = None
    reviewedAt: datetime | None = None
    createdAt: datetime


class AnalysisRunResponse(CamelModel):
    """Reproducible analysis run record with its input and method provenance."""

    id: uuid.UUID
    organisationId: uuid.UUID
    caseId: uuid.UUID | None = None
    question: str
    analysisType: str
    methodName: str
    methodVersion: str
    parameters: dict[str, Any]
    inputDatasetVersionIds: list[str]
    crs: str
    qualityMaskNotes: str | None = None
    seasonalContext: str | None = None
    limitations: str
    status: str
    requestedByUserId: uuid.UUID | None = None
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    failureReason: str | None = None
    createdAt: datetime


class AnalysisOutputResponse(CamelModel):
    """Derived analysis output awaiting human interpretation."""

    id: uuid.UUID
    analysisRunId: uuid.UUID
    outputType: str
    summary: str
    storageKey: str | None = None
    isDerived: bool
    derivedFromObservationIds: list[str]
    interpretationState: str
    limitations: str
    createdAt: datetime
