"""Pydantic boundary schemas for qualified measurements and gated verification."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.phase3Contracts import clean_required_text as _required
from ecowatch.modules.verification.enums import ExpectedDirection, MeasurementQualifier


def _decimal_text(value: Decimal | None) -> float | None:
    """Expose stored numeric measurements as JSON numbers."""
    return None if value is None else float(value)


class CreateIndicatorRequest(CamelModel):
    """Approved indicator definition criteria used by later assessments."""

    organisationId: uuid.UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=50)
    unitId: uuid.UUID
    methodName: str = Field(min_length=1, max_length=200)
    methodVersion: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=10000)
    criteriaVersion: str | None = Field(default=None, max_length=100)

    @field_validator("code", "name", "domain", "methodName", "methodVersion")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class RecordMeasurementRequest(CamelModel):
    """Qualified measurement; detection limits are recorded, never invented."""

    organisationId: uuid.UUID
    measuredAt: datetime
    qualifier: MeasurementQualifier
    unitId: uuid.UUID
    methodName: str = Field(min_length=1, max_length=200)
    methodVersion: str = Field(min_length=1, max_length=100)
    value: float | None = None
    detectionLimit: float | None = Field(default=None, ge=0)
    interventionId: uuid.UUID | None = None
    caseId: uuid.UUID | None = None
    observationId: uuid.UUID | None = None
    qualityControls: str | None = Field(default=None, max_length=10000)
    uncertaintyNote: str | None = Field(default=None, max_length=10000)
    source: str | None = Field(default=None, max_length=10000)

    @field_validator("methodName", "methodVersion")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class CreateAssessmentRequest(CamelModel):
    """Observed-change assessment; never a recovery declaration."""

    organisationId: uuid.UUID
    interventionId: uuid.UUID
    baselineMeasurementIds: list[str] = Field(default_factory=list, max_length=200)
    followUpMeasurementIds: list[str] = Field(default_factory=list, max_length=200)
    comparisonMethod: str = Field(min_length=1, max_length=10000)
    baselineValues: list[float] = Field(default_factory=list, max_length=200)
    followUpValues: list[float] = Field(default_factory=list, max_length=200)
    direction: ExpectedDirection
    minimumDetectableChange: float | None = Field(default=None, ge=0)
    uncertainty: float | None = Field(default=None, ge=0)
    confounders: str | None = Field(default=None, max_length=10000)
    seasonalityNotes: str | None = Field(default=None, max_length=10000)
    uncertaintyNote: str | None = Field(default=None, max_length=10000)
    criteriaVersion: str | None = Field(default=None, max_length=100)

    @field_validator("comparisonMethod")
    @classmethod
    def validate_comparison_method(cls, value: str) -> str:
        return _required(value)


class FinaliseAssessmentRequest(CamelModel):
    """Finalise a draft assessment with documented criteria."""

    organisationId: uuid.UUID


class RecoveryVerificationRequest(CamelModel):
    """Dedicated gated path for a two-key recovery verification."""

    organisationId: uuid.UUID
    specialistApproverUserId: uuid.UUID
    authorityApproverUserId: uuid.UUID
    criteriaVersion: str = Field(min_length=1, max_length=100)
    criteriaApproved: bool
    comparisonMethod: str = Field(min_length=1, max_length=10000)
    uncertaintyDocumented: str = Field(min_length=1, max_length=10000)
    confoundersDocumented: str = Field(min_length=1, max_length=10000)
    seasonalContextDocumented: str = Field(min_length=1, max_length=10000)

    @field_validator(
        "criteriaVersion",
        "comparisonMethod",
        "uncertaintyDocumented",
        "confoundersDocumented",
        "seasonalContextDocumented",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _required(value)


class PublishSummaryRequest(CamelModel):
    """Approved public summary with two-key approval, timestamp, and exact text."""

    organisationId: uuid.UUID
    specialistApproverUserId: uuid.UUID
    authorityApproverUserId: uuid.UUID
    publishedText: str = Field(min_length=1, max_length=10000)
    verificationAssessmentId: uuid.UUID | None = None
    caseId: uuid.UUID | None = None

    @field_validator("publishedText")
    @classmethod
    def validate_published_text(cls, value: str) -> str:
        return _required(value)


class RetractPublicationRequest(CamelModel):
    """Retraction is an audited event, not an edit to the published text."""

    organisationId: uuid.UUID
    reason: str = Field(min_length=1, max_length=10000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _required(value)


class IndicatorResponse(CamelModel):
    """Approved indicator definition with its criteria version."""

    id: uuid.UUID
    organisationId: uuid.UUID
    code: str
    name: str
    domain: str
    description: str | None = None
    unitId: uuid.UUID
    methodName: str
    methodVersion: str
    criteriaVersion: str | None = None
    approvedByUserId: uuid.UUID | None = None
    approvedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class MeasurementResponse(CamelModel):
    """Qualified measurement with resolved unit and optional detection limit."""

    id: uuid.UUID
    organisationId: uuid.UUID
    indicatorDefinitionId: uuid.UUID
    interventionId: uuid.UUID | None = None
    caseId: uuid.UUID | None = None
    observationId: uuid.UUID | None = None
    measuredAt: datetime
    value: float | None = None
    qualifier: str
    detectionLimit: float | None = None
    unitId: uuid.UUID
    methodName: str
    methodVersion: str
    qualityControls: str | None = None
    uncertaintyNote: str | None = None
    source: str | None = None
    createdAt: datetime

    @field_validator("value", "detectionLimit", mode="before")
    @classmethod
    def serialize_numeric(cls, value: Any) -> float | None:
        if isinstance(value, Decimal) or value is None:
            return _decimal_text(value)
        return _decimal_text(Decimal(str(value)))


class AssessmentResponse(CamelModel):
    """Observed-change conclusion with its criteria and review state."""

    id: uuid.UUID
    organisationId: uuid.UUID
    interventionId: uuid.UUID
    baselineMeasurementIds: list[str]
    followUpMeasurementIds: list[str]
    comparisonMethod: str
    confounders: str | None = None
    seasonalityNotes: str | None = None
    uncertaintyNote: str | None = None
    conclusion: str
    criteriaVersion: str | None = None
    status: str
    reviewedByUserId: uuid.UUID | None = None
    reviewedAt: datetime | None = None
    specialistApproverUserId: uuid.UUID | None = None
    authorityApproverUserId: uuid.UUID | None = None
    twoKeyApprovedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class PublicationResponse(CamelModel):
    """Approved public summary with approver and retraction metadata."""

    id: uuid.UUID
    organisationId: uuid.UUID
    verificationAssessmentId: uuid.UUID | None = None
    caseId: uuid.UUID | None = None
    publishedText: str
    approvedByUserId: uuid.UUID
    approvedRole: str
    approvedAt: datetime
    specialistApproverUserId: uuid.UUID | None = None
    authorityApproverUserId: uuid.UUID | None = None
    twoKeyApprovedAt: datetime | None = None
    retractedAt: datetime | None = None
    retractionReason: str | None = None
    createdAt: datetime
