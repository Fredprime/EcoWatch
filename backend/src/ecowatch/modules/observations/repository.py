"""SQLAlchemy repository for observations, versions, sources, methods, and units."""

import uuid
from typing import Any

from sqlalchemy import Uuid, column, func, inspect, or_, select, table
from sqlalchemy.orm import Session

from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.observations.models import (
    Method,
    Observation,
    ObservationSource,
    ObservationVersion,
    Unit,
)


class ObservationRepository:
    """Data-access operations for observations and controlled vocabularies."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, observationId: uuid.UUID) -> Observation | None:
        return self._session.get(Observation, observationId)

    def get_by_idempotency_key(self, idempotencyKey: uuid.UUID) -> Observation | None:
        return self._session.scalar(
            select(Observation).where(Observation.idempotencyKey == idempotencyKey)
        )

    def get_by_tracking_code_hash(self, trackingCodeHash: str) -> Observation | None:
        return self._session.scalar(
            select(Observation).where(Observation.trackingCodeHash == trackingCodeHash)
        )

    def create_observation(self, **fields: Any) -> Observation:
        observation = Observation(**fields)
        self._session.add(observation)
        self._session.flush()
        return observation

    def create_version(
        self,
        *,
        observationId: uuid.UUID,
        versionNumber: int,
        changedFields: dict[str, Any],
        reason: str,
        editedByUserId: uuid.UUID | None,
    ) -> ObservationVersion:
        version = ObservationVersion(
            observationId=observationId,
            versionNumber=versionNumber,
            changedFields=changedFields,
            reason=reason,
            editedByUserId=editedByUserId,
        )
        self._session.add(version)
        self._session.flush()
        return version

    def create_source(self, **fields: Any) -> ObservationSource:
        source = ObservationSource(**fields)
        self._session.add(source)
        self._session.flush()
        return source

    def get_source_by_observation_id(
        self, observationId: uuid.UUID
    ) -> ObservationSource | None:
        return self._session.scalar(
            select(ObservationSource).where(ObservationSource.observationId == observationId)
        )

    def list_versions(self, observationId: uuid.UUID) -> list[ObservationVersion]:
        stmt = (
            select(ObservationVersion)
            .where(ObservationVersion.observationId == observationId)
            .order_by(ObservationVersion.versionNumber.asc())
        )
        return list(self._session.scalars(stmt).all())

    def has_case_link(self, observationId: uuid.UUID) -> bool:
        """Check whether case_observations links this observation without ORM coupling."""
        bind = self._session.get_bind()
        if bind is None or not inspect(bind).has_table("case_observations"):
            return False
        caseObs = table("case_observations", column("observation_id", Uuid(as_uuid=True)))
        row = self._session.execute(
            select(caseObs.c.observation_id)
            .where(caseObs.c.observation_id == observationId)
            .limit(1)
        ).first()
        return row is not None

    def has_staff_edits(self, observation: Observation) -> bool:
        """Return True if a version > 1 was authored by someone other than the submitter."""
        stmt = select(ObservationVersion.id).where(
            ObservationVersion.observationId == observation.id,
            ObservationVersion.versionNumber > 1,
        )
        if observation.submittedByUserId is not None:
            stmt = stmt.where(
                ObservationVersion.editedByUserId != observation.submittedByUserId
            )
        return self._session.scalar(stmt.limit(1)) is not None

    def count_evidence_assets(self, observationId: uuid.UUID) -> int:
        """Return count of evidence assets linked to an observation without ORM coupling."""
        bind = self._session.get_bind()
        if bind is None or not inspect(bind).has_table("evidence_assets"):
            return 0
        assets = table("evidence_assets", column("observation_id", Uuid(as_uuid=True)))
        count = self._session.execute(
            select(func.count())
            .select_from(assets)
            .where(assets.c.observation_id == observationId)
        ).scalar_one()
        return int(count)

    def list_observations(
        self,
        *,
        organisationIds: set[uuid.UUID] | None = None,
        ownUserId: uuid.UUID | None = None,
        organisationId: uuid.UUID | None = None,
        observationType: str | None = None,
        sourceType: str | None = None,
        includeHidden: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Observation], str | None, bool]:
        if organisationIds is not None and not organisationIds and ownUserId is None:
            return [], None, False

        stmt = select(Observation)
        if organisationIds is not None:
            if ownUserId is not None and organisationIds:
                stmt = stmt.where(
                    or_(
                        Observation.organisationId.in_(organisationIds),
                        Observation.submittedByUserId == ownUserId,
                    )
                )
            elif ownUserId is not None:
                stmt = stmt.where(Observation.submittedByUserId == ownUserId)
            else:
                stmt = stmt.where(Observation.organisationId.in_(organisationIds))

        if organisationId is not None:
            stmt = stmt.where(Observation.organisationId == organisationId)
        if observationType is not None:
            stmt = stmt.where(Observation.observationType == observationType)
        if sourceType is not None:
            stmt = stmt.where(Observation.sourceType == sourceType)
        if not includeHidden:
            stmt = stmt.where(Observation.isHidden.is_(False))

        return paginate_descending(
            self._session,
            stmt,
            timeCol=Observation.receivedAt,
            idCol=Observation.id,
            cursor=cursor,
            limit=limit,
        )

    def list_for_export(self, organisationId: uuid.UUID) -> list[Observation]:
        """Return every observation for an organisation, hidden records included."""
        stmt = (
            select(Observation)
            .where(Observation.organisationId == organisationId)
            .order_by(Observation.receivedAt.asc(), Observation.id.asc())
        )
        return list(self._session.scalars(stmt).all())

    def anonymise_source(self, observationId: uuid.UUID) -> bool:
        """Clear contributor identity/contact PII on the isolated source record, keeping the row."""
        source = self.get_source_by_observation_id(observationId)
        if source is None:
            return False
        source.reporterName = None
        source.contactChannel = None
        source.contactValue = None
        source.clientMetadata = None
        self._session.flush()
        return True

    def get_method_by_id(self, methodId: uuid.UUID) -> Method | None:
        return self._session.get(Method, methodId)

    def get_method_by_code(self, code: str) -> Method | None:
        return self._session.scalar(select(Method).where(Method.code == code.strip()))

    def create_method(
        self,
        *,
        code: str,
        name: str,
        version: str,
        protocolText: str | None = None,
        instrumentClass: str | None = None,
    ) -> Method:
        method = Method(
            code=code.strip(),
            name=name.strip(),
            version=version.strip(),
            protocolText=protocolText,
            instrumentClass=instrumentClass.strip() if instrumentClass else None,
        )
        self._session.add(method)
        self._session.flush()
        return method

    def list_methods(
        self, *, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[Method], str | None, bool]:
        return paginate_descending(
            self._session,
            select(Method),
            timeCol=Method.createdAt,
            idCol=Method.id,
            cursor=cursor,
            limit=limit,
        )

    def get_unit_by_id(self, unitId: uuid.UUID) -> Unit | None:
        return self._session.get(Unit, unitId)

    def get_unit_by_symbol(self, symbol: str) -> Unit | None:
        return self._session.scalar(select(Unit).where(Unit.symbol == symbol.strip()))

    def create_unit(
        self,
        *,
        symbol: str,
        name: str,
        dimension: str,
        ucumCode: str | None = None,
    ) -> Unit:
        unit = Unit(
            symbol=symbol.strip(),
            name=name.strip(),
            dimension=dimension.strip(),
            ucumCode=ucumCode.strip() if ucumCode else None,
        )
        self._session.add(unit)
        self._session.flush()
        return unit

    def list_units(
        self, *, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[Unit], str | None, bool]:
        return paginate_descending(
            self._session,
            select(Unit),
            timeCol=Unit.createdAt,
            idCol=Unit.id,
            cursor=cursor,
            limit=limit,
        )
