"""Database access and candidate retrieval for evidence correlation.

Retrieval is deliberately dialect-agnostic: a cheap SQL prefilter (organisation,
not hidden, time window) that runs on both SQLite and PostgreSQL, then an exact
distance test in Python over that bounded set.

`shortcut: distance is filtered in Python, not with ST_DWithin, so it is bounded
by the prefilter limit rather than by a GiST index. Replace with an ST_DWithin
query on PostgreSQL when candidate volumes make the bounded scan matter.`
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from ecowatch.core.spatial import geography_to_text_expr, parse_point_wkt
from ecowatch.modules.correlation.models import (
    CorrelationTask,
    EvidenceRelationship,
    RelationshipStatus,
)
from ecowatch.modules.correlation.scoring import (
    DEFAULT_RADIUS_KM,
    DEFAULT_TEMPORAL_WINDOW_HOURS,
    haversine_km,
)
from ecowatch.modules.identity.models import Organisation
from ecowatch.modules.observations.models import Observation

METHOD_VERSION = "correlation-1"
MAX_CANDIDATES = 200

_DECIDED = (
    RelationshipStatus.ACCEPTED.value,
    RelationshipStatus.REJECTED.value,
    RelationshipStatus.AMBIGUOUS.value,
)


def canonical_pair(
    firstId: uuid.UUID, secondId: uuid.UUID
) -> tuple[uuid.UUID, uuid.UUID]:
    """Order a pair the way the database check constraint requires."""
    return (firstId, secondId) if firstId < secondId else (secondId, firstId)


def require_aware(value: datetime | None, *, dialectName: str) -> datetime | None:
    """Return an aware datetime, or refuse rather than guess an offset.

    PostgreSQL returns `timestamptz` values already aware, so a naive value there
    is a real defect. SQLite has no timezone type and silently drops the offset
    the column was written with, so re-attaching UTC restores the known value.

    `shortcut: SQLite-naive is assumed to be UTC. Correct because the column is
    timestamptz in PostgreSQL, which is the only production dialect.`
    """
    if value is None or value.tzinfo is not None:
        return value
    if dialectName == "postgresql":
        raise ValueError(
            "observed_at came back naive from PostgreSQL; the column must be timestamptz"
        )
    return value.replace(tzinfo=UTC)


class CorrelationRepository:
    """Queries and writes for evidence correlation."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def dialect_name(self) -> str:
        bind = self._session.get_bind()
        return bind.dialect.name

    def get_observation(self, observationId: uuid.UUID) -> Observation | None:
        return self._session.get(Observation, observationId)

    def source_ref(self, observationId: uuid.UUID) -> str | None:
        """Original source identifier for repost/independence checks (`FR-027`)."""
        return self._session.scalar(
            select(Observation.sourceRef).where(Observation.id == observationId)
        )

    def location_wkt(self, observationId: uuid.UUID) -> Any:
        """Location as WKT text regardless of dialect."""
        expr = geography_to_text_expr(Observation.location, self.dialect_name)
        return self._session.scalar(select(expr).where(Observation.id == observationId))

    def candidate_rows(
        self,
        subject: Observation,
        *,
        limit: int = MAX_CANDIDATES,
        temporal_window_hours: float = DEFAULT_TEMPORAL_WINDOW_HOURS,
        radius_km: float = DEFAULT_RADIUS_KM,
    ) -> list[tuple[Observation, Any]]:
        """Return bounded candidates for `subject` as (observation, location WKT).

        Organisation scoping and the hidden flag are applied here, so a caller
        cannot accidentally retrieve across tenants.
        """
        statement: Select[Any] = select(
            Observation,
            geography_to_text_expr(Observation.location, self.dialect_name),
        ).where(
            Observation.organisationId == subject.organisationId,
            Observation.id != subject.id,
            Observation.isHidden.is_(False),
        )

        subjectObservedAt = require_aware(subject.observedAt, dialectName=self.dialect_name)
        if subjectObservedAt is not None:
            window = timedelta(hours=temporal_window_hours)
            statement = statement.where(
                Observation.observedAt.is_not(None),
                Observation.observedAt >= subjectObservedAt - window,
                Observation.observedAt <= subjectObservedAt + window,
            )

        statement = statement.order_by(Observation.receivedAt.desc()).limit(limit)

        subjectPoint = parse_point_wkt(self.location_wkt(subject.id))
        rows: list[tuple[Observation, Any]] = []
        for row in self._session.execute(statement).all():
            candidate, candidateWkt = row[0], row[1]
            if subjectPoint is not None and candidateWkt is not None:
                point = parse_point_wkt(candidateWkt)
                if point is not None:
                    distance = haversine_km(
                        subjectPoint[1], subjectPoint[0], point[1], point[0]
                    )
                    if distance > radius_km:
                        continue
            rows.append((candidate, candidateWkt))
        return rows

    def decided_partner_ids(self, observationId: uuid.UUID) -> set[uuid.UUID]:
        """Partners already ruled on by a human; they must not be re-suggested."""
        rows = self._session.execute(
            select(EvidenceRelationship.observationAId, EvidenceRelationship.observationBId).where(
                or_(
                    EvidenceRelationship.observationAId == observationId,
                    EvidenceRelationship.observationBId == observationId,
                ),
                EvidenceRelationship.status.in_(_DECIDED),
            )
        ).all()
        return {
            second if first == observationId else first for first, second in rows
        }

    def get_relationship(self, relationshipId: uuid.UUID) -> EvidenceRelationship | None:
        return self._session.get(EvidenceRelationship, relationshipId)

    def find_pair(
        self, firstId: uuid.UUID, secondId: uuid.UUID, task: str
    ) -> EvidenceRelationship | None:
        aId, bId = canonical_pair(firstId, secondId)
        return self._session.scalar(
            select(EvidenceRelationship).where(
                EvidenceRelationship.observationAId == aId,
                EvidenceRelationship.observationBId == bId,
                EvidenceRelationship.task == task,
            )
        )

    def upsert_suggestion(
        self,
        *,
        organisationId: uuid.UUID,
        firstId: uuid.UUID,
        secondId: uuid.UUID,
        task: str,
        score: float,
        components: dict[str, float],
        missingSignals: list[str],
        reasons: list[str],
        sourceIndependent: bool,
        methodVersion: str = METHOD_VERSION,
    ) -> EvidenceRelationship:
        """Insert a suggestion, or refresh an undecided one. Decisions are never overwritten."""
        aId, bId = canonical_pair(firstId, secondId)
        existing = self.find_pair(aId, bId, task)
        if existing is not None:
            if existing.status != RelationshipStatus.SUGGESTED.value:
                return existing
            existing.score = score
            existing.components = components
            existing.missingSignals = missingSignals
            existing.reasons = reasons
            existing.sourceIndependent = sourceIndependent
            existing.methodVersion = methodVersion
            self._session.flush()
            return existing

        relationship = EvidenceRelationship(
            organisationId=organisationId,
            observationAId=aId,
            observationBId=bId,
            task=task,
            score=score,
            components=components,
            missingSignals=missingSignals,
            reasons=reasons,
            sourceIndependent=sourceIndependent,
            methodVersion=methodVersion,
            status=RelationshipStatus.SUGGESTED.value,
        )
        self._session.add(relationship)
        self._session.flush()
        return relationship

    def list_suggestions(
        self, organisationIds: set[uuid.UUID], *, limit: int = 50
    ) -> list[EvidenceRelationship]:
        """Undecided suggestions for the caller's organisations, best first."""
        if not organisationIds:
            return []
        return list(
            self._session.scalars(
                select(EvidenceRelationship)
                .where(
                    EvidenceRelationship.organisationId.in_(organisationIds),
                    EvidenceRelationship.status == RelationshipStatus.SUGGESTED.value,
                )
                .order_by(EvidenceRelationship.score.desc(), EvidenceRelationship.createdAt.desc())
                .limit(limit)
            ).all()
        )

    def all_org_ids(self) -> set[uuid.UUID]:
        """Every organisation id, for a platform administrator's view only."""
        return set(self._session.scalars(select(Organisation.id)).all())

    def count_for_task(self, task: CorrelationTask) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(EvidenceRelationship)
                .where(EvidenceRelationship.task == task.value)
            )
            or 0
        )

