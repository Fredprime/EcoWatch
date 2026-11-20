"""Pydantic boundary schemas for the intervention lifecycle."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.core.spatial import validate_wkt_geometry
from ecowatch.modules.interventions.enums import InterventionStatus
from ecowatch.modules.phase3Contracts import clean_required_text as _required
from ecowatch.modules.phase3Contracts import geometry_text as _geometry_text


class CreateInterventionRequest(CamelModel):
    """Accountable intervention record with an explicit activity baseline."""

    organisationId: uuid.UUID
    caseId: uuid.UUID
    objective: str = Field(min_length=1, max_length=10000)
    responsibleOrganisationId: uuid.UUID
    authorisedLeadUserId: uuid.UUID
    plannedStartAt: datetime | None = None
    plannedEndAt: datetime | None = None
    rationale: str | None = Field(default=None, max_length=10000)
    approvalReference: str | None = Field(default=None, max_length=10000)
    location: str | None = Field(default=None, max_length=50000)
    affectedAreaNotes: str | None = Field(default=None, max_length=10000)
    intendedOutcome: str | None = Field(default=None, max_length=10000)
    indicatorDefinitionIds: list[str] = Field(default_factory=list, max_length=200)
    baselineSummary: str | None = Field(default=None, max_length=10000)
    risks: str | None = Field(default=None, max_length=10000)
    limitations: str | None = Field(default=None, max_length=10000)
    followUpSchedule: str | None = Field(default=None, max_length=10000)
    additionalCaseIds: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("objective")
    @classmethod
    def validate_objective(cls, value: str) -> str:
        return _required(value)

    @field_validator("location", mode="before")
    @classmethod
    def validate_location(cls, value: Any) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return validate_wkt_geometry(str(value))


class AddMilestoneRequest(CamelModel):
    """Planned intervention milestone; completion is a separate action."""

    organisationId: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    plannedAt: datetime | None = None
    description: str | None = Field(default=None, max_length=10000)
    evidenceAssetIds: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _required(value)


class CompleteMilestoneRequest(CamelModel):
    """Complete a milestone; only activity status may be derived, never outcome."""

    organisationId: uuid.UUID
    evidenceAssetIds: list[str] = Field(default_factory=list, max_length=200)


class TransitionInterventionRequest(CamelModel):
    """Explicit intervention status transition with rationale."""

    organisationId: uuid.UUID
    targetStatus: InterventionStatus
    rationale: str = Field(min_length=1, max_length=10000)
    verificationAssessmentRef: str | None = Field(default=None, max_length=10000)

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _required(value)


class InterventionResponse(CamelModel):
    """Staff view of an intervention and its accountable ownership."""

    id: uuid.UUID
    organisationId: uuid.UUID
    caseId: uuid.UUID
    additionalCaseIds: list[str]
    objective: str
    rationale: str | None = None
    responsibleOrganisationId: uuid.UUID
    authorisedLeadUserId: uuid.UUID
    approvalReference: str | None = None
    location: str | None = None
    affectedAreaNotes: str | None = None
    plannedStartAt: datetime | None = None
    plannedEndAt: datetime | None = None
    actualStartAt: datetime | None = None
    actualEndAt: datetime | None = None
    status: str
    resourcesNotes: str | None = None
    intendedOutcome: str | None = None
    indicatorDefinitionIds: list[str]
    baselineSummary: str | None = None
    risks: str | None = None
    limitations: str | None = None
    followUpSchedule: str | None = None
    verificationAssessmentId: uuid.UUID | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_validator("location", mode="before")
    @classmethod
    def serialize_location(cls, value: Any) -> str | None:
        return _geometry_text(value)


class MilestoneResponse(CamelModel):
    """Intervention milestone with explicit planned and completed timestamps."""

    id: uuid.UUID
    interventionId: uuid.UUID
    name: str
    description: str | None = None
    plannedAt: datetime | None = None
    completedAt: datetime | None = None
    status: str
    evidenceAssetIds: list[str]
    createdAt: datetime
    updatedAt: datetime
