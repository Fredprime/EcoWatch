"""SQLAlchemy repository for evidence assets and derivatives."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.modules.evidence.models import AssetDerivative, EvidenceAsset


class EvidenceRepository:
    """Data-access operations for evidence_assets and asset_derivatives."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_asset_by_id(self, assetId: uuid.UUID) -> EvidenceAsset | None:
        return self._session.get(EvidenceAsset, assetId)

    def create_asset(self, **fields: Any) -> EvidenceAsset:
        asset = EvidenceAsset(**fields)
        self._session.add(asset)
        self._session.flush()
        return asset

    def get_asset_by_idempotency_key(
        self, observationId: uuid.UUID, idempotencyKey: uuid.UUID
    ) -> EvidenceAsset | None:
        """Return the asset created for a replayed media upload, if any."""
        return self._session.scalar(
            select(EvidenceAsset).where(
                EvidenceAsset.observationId == observationId,
                EvidenceAsset.idempotencyKey == idempotencyKey,
            )
        )

    def list_assets_for_observation(
        self, observationId: uuid.UUID
    ) -> list[EvidenceAsset]:
        stmt = (
            select(EvidenceAsset)
            .where(EvidenceAsset.observationId == observationId)
            .order_by(EvidenceAsset.createdAt.asc())
        )
        return list(self._session.scalars(stmt).all())

    def get_derivative_by_id(self, derivativeId: uuid.UUID) -> AssetDerivative | None:
        return self._session.get(AssetDerivative, derivativeId)

    def list_derivatives_for_asset(
        self, parentAssetId: uuid.UUID
    ) -> list[AssetDerivative]:
        stmt = (
            select(AssetDerivative)
            .where(AssetDerivative.parentAssetId == parentAssetId)
            .order_by(AssetDerivative.createdAt.asc())
        )
        return list(self._session.scalars(stmt).all())

    def create_derivative(self, **fields: Any) -> AssetDerivative:
        derivative = AssetDerivative(**fields)
        self._session.add(derivative)
        self._session.flush()
        return derivative
