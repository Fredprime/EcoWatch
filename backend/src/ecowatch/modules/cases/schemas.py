"""Pydantic boundary schemas for investigation cases, links, timelines, and public summaries."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.core.spatial import validate_wkt_geometry
from ecowatch.modules.cases.models import CaseStatus, LinkProposedBy, LinkReviewStatus


def _serialize_geometry(value: Any) -> str | None:
    """Normalise optional stored geometry values to WKT strings."""
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _validate_optional_wkt(value: str | None) -> str | None:
    """Validate optional WKT geometry input without inventing coordinates."""
    if value is None:
        return None
    cleaned = value.strip()
    return validate_wkt_geometry(cleaned) if cleaned else None


def _strip_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Value must not be blank")
    return cleaned


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _strip_string_list(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    return [item.strip() for item in values if item.strip()]


class FieldVerificationApprovalRole(StrEnum):
    """Explicit key slot for two-key field verification approval."""

    SPECIALIST = "specialist"
    AUTHORITY = "authority"


class CreateCaseRequest(CamelModel):
    """Request payload to create a new investigation case."""

    organisationId: uuid.UUID
    caseCode: str | None = Field(default=None, min_length=3, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=10000)
    status: CaseStatus = CaseStatus.NEW_UNREVIEWED
    statusRationale: str = Field(default="Initial case creation", min_length=1, max_length=4000)
    areaGeometry: str | None = Field(default=None, max_length=50000)
    publicGeometry: str | None = Field(default=None, max_length=50000)
    areaReference: str | None = Field(default=None, max_length=200)
    leadInvestigatorId: uuid.UUID | None = None
    investigationQuestions: list[str] = Field(default_factory=list, max_length=50)
    competingHypotheses: list[str] = Field(default_factory=list, max_length=50)
    evidenceGaps: list[str] = Field(default_factory=list, max_length=50)
    accessClass: str = Field(default="internal", min_length=1, max_length=32)
    publicSummary: str | None = Field(default=None, max_length=10000)

    @field_validator("title", "summary", "statusRationale", "accessClass")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("caseCode", "areaReference", "publicSummary")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("areaGeometry", "publicGeometry")
    @classmethod
    def validate_geometries(cls, value: str | None) -> str | None:
        return _validate_optional_wkt(value)

    @field_validator("investigationQuestions", "competingHypotheses", "evidenceGaps")
    @classmethod
    def validate_string_lists(cls, values: list[str]) -> list[str]:
        return [item.strip() for item in values if item.strip()]


class UpdateCaseRequest(CamelModel):
    """Partial update payload for investigation metadata, assignment, and public draft."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, min_length=1, max_length=10000)
    areaGeometry: str | None = Field(default=None, max_length=50000)
    publicGeometry: str | None = Field(default=None, max_length=50000)
    areaReference: str | None = Field(default=None, max_length=200)
    leadInvestigatorId: uuid.UUID | None = None
    investigationQuestions: list[str] | None = Field(default=None, max_length=50)
    competingHypotheses: list[str] | None = Field(default=None, max_length=50)
    evidenceGaps: list[str] | None = Field(default=None, max_length=50)
    fieldRecordReference: str | None = Field(default=None, max_length=200)
    referralRecord: dict[str, Any] | None = None
    accessClass: str | None = Field(default=None, min_length=1, max_length=32)
    publicSummary: str | None = Field(default=None, max_length=10000)
    isPublicSummaryApproved: bool | None = None

    @field_validator("title", "summary", "accessClass")
    @classmethod
    def validate_non_blank_when_present(cls, value: str | None) -> str | None:
        return None if value is None else _strip_required(value)

    @field_validator("areaReference", "fieldRecordReference", "publicSummary")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("areaGeometry", "publicGeometry")
    @classmethod
    def validate_geometries(cls, value: str | None) -> str | None:
        return _validate_optional_wkt(value)

    @field_validator("investigationQuestions", "competingHypotheses", "evidenceGaps")
    @classmethod
    def validate_string_lists(cls, values: list[str] | None) -> list[str] | None:
        return _strip_string_list(values)


class TransitionCaseStatusRequest(CamelModel):
    """Payload to advance or conclude a case status with rationale and preconditions."""

    status: CaseStatus
    statusRationale: str | None = Field(default=None, max_length=4000)
    referralRecord: dict[str, Any] | None = None
    fieldRecordReference: str | None = Field(default=None, max_length=200)
    mergedIntoCaseId: uuid.UUID | None = None

    @field_validator("statusRationale", "fieldRecordReference")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class FieldVerificationApprovalRequest(CamelModel):
    """Payload for recording an ES or OA two-key field verification approval."""

    approvalRole: FieldVerificationApprovalRole | None = None
    fieldRecordReference: str | None = Field(default=None, max_length=200)
    rationale: str | None = Field(default=None, max_length=4000)

    @field_validator("fieldRecordReference", "rationale")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class FieldVerificationApprovalResponse(CamelModel):
    """Current two-key approval state for a case's field verification."""

    caseId: uuid.UUID
    status: CaseStatus
    fieldRecordReference: str | None = None
    specialistApprovalUserId: uuid.UUID | None = None
    authorityApprovalUserId: uuid.UUID | None = None
    readyForFieldVerified: bool


class LinkObservationRequest(CamelModel):
    """Request payload to link an existing observation to a case."""

    observationId: uuid.UUID
    linkRationale: str = Field(min_length=1, max_length=4000)
    proposedByType: LinkProposedBy = LinkProposedBy.HUMAN
    reviewStatus: LinkReviewStatus = LinkReviewStatus.ACCEPTED
    isContested: bool = False
    contestedNote: str | None = Field(default=None, max_length=4000)

    @field_validator("linkRationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("contestedNote")
    @classmethod
    def validate_contested_note(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class UpdateCaseObservationRequest(CamelModel):
    """Request payload to update review status or contest state on a case-observation link."""

    linkRationale: str | None = Field(default=None, min_length=1, max_length=4000)
    reviewStatus: LinkReviewStatus | None = None
    isContested: bool | None = None
    contestedNote: str | None = Field(default=None, max_length=4000)

    @field_validator("linkRationale")
    @classmethod
    def validate_rationale(cls, value: str | None) -> str | None:
        return None if value is None else _strip_required(value)

    @field_validator("contestedNote")
    @classmethod
    def validate_contested_note(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class CaseObservationResponse(CamelModel):
    """Staff representation of a case-to-observation link."""

    id: uuid.UUID
    caseId: uuid.UUID
    observationId: uuid.UUID
    linkRationale: str
    proposedByType: LinkProposedBy
    proposedByUserId: uuid.UUID | None = None
    reviewStatus: LinkReviewStatus
    reviewedByUserId: uuid.UUID | None = None
    reviewedAt: datetime | None = None
    isContested: bool
    contestedNote: str | None = None
    createdAt: datetime
    updatedAt: datetime


class CaseResponse(CamelModel):
    """Staff representation of an investigation case."""

    id: uuid.UUID
    organisationId: uuid.UUID
    caseCode: str
    title: str
    summary: str
    status: CaseStatus
    statusRationale: str
    areaGeometry: str | None = None
    publicGeometry: str | None = None
    areaReference: str | None = None
    leadInvestigatorId: uuid.UUID | None = None
    investigationQuestions: list[str]
    competingHypotheses: list[str]
    evidenceGaps: list[str]
    referralRecord: dict[str, Any] | None = None
    fieldRecordReference: str | None = None
    specialistApprovalUserId: uuid.UUID | None = None
    authorityApprovalUserId: uuid.UUID | None = None
    mergedIntoCaseId: uuid.UUID | None = None
    accessClass: str
    isPublicSummaryApproved: bool
    publicSummary: str | None = None
    createdByUserId: uuid.UUID
    lastReviewedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_validator("areaGeometry", "publicGeometry", mode="before")
    @classmethod
    def serialize_geometry(cls, value: Any) -> str | None:
        return _serialize_geometry(value)


class CaseDetailResponse(CaseResponse):
    """Detailed case view including linked observation records."""

    observations: list[CaseObservationResponse] = Field(default_factory=list)


class TimelineItemResponse(CamelModel):
    """Chronological timeline entry with explicit date semantics, precision, and source."""

    dateType: str
    timestamp: datetime
    precision: str
    source: str
    entityType: str
    entityId: uuid.UUID
    summary: str | None = None


class PublicCaseResponse(CamelModel):
    """Redacted public case summary excluding internal notes, geometries, and identities."""

    id: uuid.UUID
    caseCode: str
    title: str
    status: CaseStatus
    publicSummary: str
    publicGeometry: str | None = None
    areaReference: str | None = None
    lastReviewedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_validator("publicGeometry", mode="before")
    @classmethod
    def serialize_geometry(cls, value: Any) -> str | None:
        return _serialize_geometry(value)
