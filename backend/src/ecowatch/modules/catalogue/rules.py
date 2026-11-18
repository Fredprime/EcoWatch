"""Domain rules for dataset rights and version completeness."""

from __future__ import annotations

from datetime import datetime

from ecowatch.core.errors import DomainError, ErrorCode


def assert_dataset_version_complete(
    *,
    licence: str | None,
    attribution: str | None,
    permittedUse: str | None,
    sourceAcquisitionAt: datetime | None,
    coverageStartAt: datetime | None,
    coverageEndAt: datetime | None,
    crs: str | None,
    resolution: str | None,
    method: str | None,
) -> None:
    """Require full provenance and rights before a dataset version is stored."""
    requiredText = {
        "licence": licence,
        "attribution": attribution,
        "permittedUse": permittedUse,
        "crs": crs,
        "resolution": resolution,
        "method": method,
    }
    for fieldName, value in requiredText.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required for a dataset version.",
                field=fieldName,
            )

    if sourceAcquisitionAt is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "sourceAcquisitionAt is required for a dataset version.",
            field="sourceAcquisitionAt",
        )

    if (
        coverageStartAt is not None
        and coverageEndAt is not None
        and coverageStartAt > coverageEndAt
    ):
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "coverageStartAt must not be after coverageEndAt.",
            field="coverageEndAt",
        )


def assert_dataset_rights_recorded(
    *,
    licence: str | None,
    attribution: str | None,
    permittedUse: str | None,
) -> None:
    """Require licence, attribution, and permitted use before a dataset is used."""
    for fieldName, value in {
        "licence": licence,
        "attribution": attribution,
        "permittedUse": permittedUse,
    }.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required before a dataset is used.",
                field=fieldName,
            )
