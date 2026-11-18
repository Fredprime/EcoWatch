"""Service layer for the environmental data catalogue."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.catalogue import models, rules
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.phase3Contracts import record_event, require_permission, require_text


class CatalogueService:
    """Create rights-recorded datasets and immutable dataset versions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_dataset(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        name: str,
        owner: str,
        licence: str,
        attribution: str,
        permittedUse: str,
        crs: str,
        description: str | None = None,
        coverageStartAt: datetime | None = None,
        coverageEndAt: datetime | None = None,
        coverageGeometry: Any | None = None,
        requestId: str | None = None,
    ) -> models.Dataset:
        """Create a dataset only when licence, attribution, and permitted use exist."""
        require_permission(principal, Permission.CATALOGUE_WRITE, organisationId)
        require_text(name, "name")
        require_text(owner, "owner")
        rules.assert_dataset_rights_recorded(
            licence=licence,
            attribution=attribution,
            permittedUse=permittedUse,
        )
        require_text(crs, "crs")
        record = models.Dataset(
            organisationId=organisationId,
            name=name.strip(),
            description=description,
            owner=owner.strip(),
            licence=licence.strip(),
            attribution=attribution.strip(),
            permittedUse=permittedUse.strip(),
            crs=crs.strip(),
            coverageStartAt=coverageStartAt,
            coverageEndAt=coverageEndAt,
            coverageGeometry=coverageGeometry,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="catalogue.dataset.created",
            targetType="dataset",
            targetId=record.id,
            detail={"name": record.name},
            requestId=requestId,
        )
        return record

    def add_dataset_version(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        datasetId: UUID,
        versionLabel: str,
        sourceAcquisitionAt: datetime,
        resolution: str,
        crs: str,
        method: str,
        licence: str,
        attribution: str,
        permittedUse: str,
        limitations: str | None = None,
        qualityNotes: str | None = None,
        checksum: str | None = None,
        storageKey: str | None = None,
        requestId: str | None = None,
    ) -> models.DatasetVersion:
        """Append a complete, non-duplicate version snapshot to a dataset."""
        require_permission(principal, Permission.CATALOGUE_WRITE, organisationId)
        require_text(versionLabel, "versionLabel")
        parent = self._session.get(models.Dataset, datasetId)
        if parent is None or parent.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Dataset not found.",
                statusCode=404,
                field="datasetId",
            )
        rules.assert_dataset_version_complete(
            licence=licence,
            attribution=attribution,
            permittedUse=permittedUse,
            sourceAcquisitionAt=sourceAcquisitionAt,
            coverageStartAt=parent.coverageStartAt,
            coverageEndAt=parent.coverageEndAt,
            crs=crs,
            resolution=resolution,
            method=method,
        )
        duplicate = self._session.scalar(
            select(models.DatasetVersion.id).where(
                models.DatasetVersion.datasetId == datasetId,
                models.DatasetVersion.versionLabel == versionLabel,
            )
        )
        if duplicate is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A dataset version with this label already exists.",
                field="versionLabel",
            )
        record = models.DatasetVersion(
            datasetId=datasetId,
            versionLabel=versionLabel.strip(),
            sourceAcquisitionAt=sourceAcquisitionAt,
            resolution=resolution.strip(),
            crs=crs.strip(),
            method=method.strip(),
            limitations=limitations,
            qualityNotes=qualityNotes,
            licenceSnapshot=licence.strip(),
            attributionSnapshot=attribution.strip(),
            permittedUseSnapshot=permittedUse.strip(),
            checksum=checksum,
            storageKey=storageKey,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="catalogue.datasetVersion.created",
            targetType="datasetVersion",
            targetId=record.id,
            detail={"datasetId": str(datasetId), "versionLabel": record.versionLabel},
            requestId=requestId,
        )
        return record
