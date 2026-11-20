"""Domain rules for evidence-backed relationships and reproducible analysis."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.intelligence import enums

SUMMARY_METHOD_NAME = "stored-value-descriptive-summary"
SUMMARY_METHOD_VERSION = "1.0"
MAX_STORED_DATASET_BYTES = 25 * 1024 * 1024
MAX_SUMMARY_RECORDS = 100_000
SUMMARY_LIMITATIONS_CAVEAT = (
    "Mechanical descriptive summary of stored dataset values only; awaiting human "
    "interpretation. This output states no pollution source, causal link, harm, "
    "severity, verification or legal conclusion."
)


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


def parse_stored_dataset_records(data: bytes, storageKey: str) -> list[dict[str, Any]]:
    """Parse bounded CSV or JSON dataset bytes into row mappings, or fail explicitly.

    Content is treated strictly as data: no evaluation, no path use. Only UTF-8
    arrays of objects (optionally under a top-level "records" key) or CSV rows are
    accepted, so a partial or unsupported payload never yields a fabricated summary.
    """
    fieldName = "inputDatasetVersionIds"
    if not data:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, "Stored dataset has no content.", field=fieldName
        )
    if len(data) > MAX_STORED_DATASET_BYTES:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Stored dataset exceeds the maximum supported size.",
            field=fieldName,
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Stored dataset is not UTF-8 text.",
            field=fieldName,
        ) from error

    stripped = text.lstrip()
    try:
        if stripped.startswith(("{", "[")):
            parsed: Any = json.loads(text)
            if isinstance(parsed, dict):
                parsed = parsed.get("records")
            if not isinstance(parsed, list):
                raise ValueError("JSON dataset must be an array of objects")
        else:
            parsed = list(csv.DictReader(io.StringIO(text)))
    except (json.JSONDecodeError, csv.Error, ValueError) as error:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"Stored dataset at {storageKey} could not be parsed as CSV or JSON.",
            field=fieldName,
        ) from error

    if len(parsed) > MAX_SUMMARY_RECORDS:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Stored dataset exceeds the maximum supported row count.",
            field=fieldName,
        )
    if not parsed:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Stored dataset contains no records.",
            field=fieldName,
        )

    records: list[dict[str, Any]] = []
    for row in parsed:
        if not isinstance(row, dict):
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Stored dataset contains a record that is not an object.",
                field=fieldName,
            )
        records.append({str(key): value for key, value in row.items()})
    return records


def build_stored_value_summary(
    records: list[dict[str, Any]],
    *,
    declaredMethodName: str,
    declaredMethodVersion: str,
) -> dict[str, Any]:
    """Build a deterministic, interpretation-free summary of stored record values."""
    columns = sorted({key for row in records for key in row})
    columnSummaries: dict[str, Any] = {}
    missingPresent = False
    numericPresent = False
    for column in columns:
        values = [row.get(column) for row in records]
        missing = sum(
            1
            for value in values
            if value is None or (isinstance(value, str) and not value.strip())
        )
        numeric: list[float] = []
        for value in values:
            if isinstance(value, bool) or value is None:
                continue
            if isinstance(value, (int, float)):
                numeric.append(float(value))
            elif isinstance(value, str) and value.strip():
                try:
                    numeric.append(float(value.strip()))
                except ValueError:
                    continue
        missingPresent = missingPresent or missing > 0
        numericPresent = numericPresent or len(numeric) > 0
        summary: dict[str, Any] = {
            "count": len(values) - missing,
            "missingCount": missing,
            "numericCount": len(numeric),
        }
        if numeric:
            summary["min"] = min(numeric)
            summary["max"] = max(numeric)
            summary["mean"] = round(sum(numeric) / len(numeric), 6)
        columnSummaries[column] = summary

    return {
        "computationMethod": {
            "name": SUMMARY_METHOD_NAME,
            "version": SUMMARY_METHOD_VERSION,
        },
        "declaredMethod": {
            "name": declaredMethodName,
            "version": declaredMethodVersion,
        },
        "note": (
            "Mechanical summary of stored input dataset values. It is not the "
            "declared scientific method result and is not evidence of any source, "
            "causal link, harm, severity, verification or legal conclusion."
        ),
        "recordCount": len(records),
        "columnCount": len(columns),
        "qualityFlags": {
            "missingValuesPresent": missingPresent,
            "numericValuesPresent": numericPresent,
        },
        "columns": columnSummaries,
    }
