"""Domain rules for evidence-backed relationships and reproducible analysis."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.intelligence import enums


def require_enum(
    enumClass: type[StrEnum],
    value: str | StrEnum | None,
    fieldName: str,
) -> StrEnum:
    """Resolve a value against an enumeration or raise a field-level error."""
    if value is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, f"{fieldName} is required.", field=fieldName
        )
    try:
        return enumClass(value)
    except ValueError as error:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"{fieldName} has an unsupported value.",
            field=fieldName,
        ) from error


def assert_environmental_relationship_valid(
    *,
    relationshipType: str | enums.EnvironmentalRelationshipType | None,
    fromEntityId: object | None,
    fromObservationId: object | None,
    toEntityId: object | None,
    toObservationId: object | None,
    evidenceSummary: str | None,
    uncertainty: str | enums.UncertaintyLevel | None,
    uncertaintyNote: str | None,
    alternativeExplanations: str | None,
    methodName: str | None,
    methodVersion: str | None,
) -> None:
    """Require one endpoint per side plus evidence, uncertainty, and alternatives."""
    require_enum(enums.EnvironmentalRelationshipType, relationshipType, "relationshipType")
    require_enum(enums.UncertaintyLevel, uncertainty, "uncertainty")

    fromEndpoints = [value for value in (fromEntityId, fromObservationId) if value is not None]
    toEndpoints = [value for value in (toEntityId, toObservationId) if value is not None]
    if len(fromEndpoints) != 1:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Exactly one source endpoint is required.",
            field="fromEntityId",
        )
    if len(toEndpoints) != 1:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Exactly one target endpoint is required.",
            field="toEntityId",
        )

    for fieldName, value in {
        "evidenceSummary": evidenceSummary,
        "uncertaintyNote": uncertaintyNote,
        "alternativeExplanations": alternativeExplanations,
        "methodName": methodName,
        "methodVersion": methodVersion,
    }.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required for an environmental relationship.",
                field=fieldName,
            )


def assert_analysis_run_reproducible(
    *,
    question: str | None,
    analysisType: str | enums.AnalysisType | None,
    methodName: str | None,
    methodVersion: str | None,
    inputDatasetVersionIds: list[str] | None,
    crs: str | None,
    parameters: dict[str, Any] | None,
    limitations: str | None,
) -> None:
    """Require every input needed to reproduce an analysis run."""
    require_enum(enums.AnalysisType, analysisType, "analysisType")
    for fieldName, value in {
        "question": question,
        "methodName": methodName,
        "methodVersion": methodVersion,
        "crs": crs,
        "limitations": limitations,
    }.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required for a reproducible analysis run.",
                field=fieldName,
            )
    if not inputDatasetVersionIds:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "At least one input dataset version is required.",
            field="inputDatasetVersionIds",
        )
    if parameters is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Analysis parameters are required.",
            field="parameters",
        )


def assert_derived_output(
    *,
    analysisRunId: object | None,
    outputType: str | enums.AnalysisOutputType | None,
    summary: str | None,
    limitations: str | None,
) -> None:
    """Require an analysis output to link to a run and state its limitations."""
    if analysisRunId is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "An analysis output must link to an analysis run.",
            field="analysisRunId",
        )
    require_enum(enums.AnalysisOutputType, outputType, "outputType")
    for fieldName, value in {"summary": summary, "limitations": limitations}.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required for an analysis output.",
                field=fieldName,
            )


def assert_prediction_allowed(
    *,
    modelName: str | None,
    modelVersion: str | None,
    validationReportRef: str | None,
    representativeDataRef: str | None,
    targetDefined: bool,
) -> None:
    """Block predictive analysis until a validated, representative model exists."""
    missing = [
        fieldName
        for fieldName, value in {
            "modelName": modelName,
            "modelVersion": modelVersion,
            "validationReportRef": validationReportRef,
            "representativeDataRef": representativeDataRef,
        }.items()
        if value is None or not value.strip()
    ]
    if not targetDefined:
        missing.append("targetDefined")
    if missing:
        raise DomainError(
            ErrorCode.PREDICTION_BLOCKED,
            "Predictive analysis is blocked until a validated model and "
            "representative data are registered.",
            field=missing[0],
        )


def assert_temporal_scope(
    temporalStartAt: datetime | None,
    temporalEndAt: datetime | None,
) -> None:
    """Reject a temporal scope whose start follows its end."""
    if (
        temporalStartAt is not None
        and temporalEndAt is not None
        and temporalStartAt > temporalEndAt
    ):
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "temporalStartAt must not be after temporalEndAt.",
            field="temporalEndAt",
        )
