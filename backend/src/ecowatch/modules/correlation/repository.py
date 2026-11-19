"""Database access and candidate retrieval for evidence correlation.

Retrieval is a prefilter (organisation, not hidden, time window) plus an exact
distance test. The bounds themselves come from `policy.py`, so retrieval and
scoring cannot disagree about how wide a scan is.

On PostgreSQL the distance test is `ST_DWithin` against `geography`, so it uses
the GiST index Phase 1 created and the LIMIT applies to rows that already pass.

`shortcut: SQLite has no spatial functions, so there the distance test is a
haversine in Python over the prefiltered, limited set. Correct, just bounded by
the prefilter rather than by an index. SQLite is the test dialect only.`
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, or_, select, text
from sqlalchemy.orm import Session

from ecowatch.core.spatial import (
    format_point_wkt,
    geography_to_text_expr,
    parse_point_wkt,
)
from ecowatch.modules.correlation.embeddings import VECTOR_MODEL_VERSION
from ecowatch.modules.correlation.models import (
    CorrelationCluster,
    CorrelationClusterMember,
    CorrelationEmbedding,
    CorrelationTask,
    EvidenceRelationship,
    RelationshipStatus,
)
from ecowatch.modules.correlation.policy import RetrievalPolicy, policy_for
from ecowatch.modules.correlation.scoring import haversine_km
from ecowatch.modules.identity.models import Organisation
from ecowatch.modules.observations.models import Observation

METHOD_VERSION = "correlation-2"
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

    def current_embedding(self, observationId: uuid.UUID) -> CorrelationEmbedding | None:
        """Latest stored vector for the active model version."""
        return self._session.scalar(
            select(CorrelationEmbedding)
            .where(
                CorrelationEmbedding.observationId == observationId,
                CorrelationEmbedding.modelVersion == VECTOR_MODEL_VERSION,
            )
            .order_by(CorrelationEmbedding.createdAt.desc(), CorrelationEmbedding.id.desc())
            .limit(1)
        )

    def embedding_for_observation(
        self, observationId: uuid.UUID
    ) -> tuple[float, ...] | None:
        embedding = self.current_embedding(observationId)
        return tuple(embedding.embedding) if embedding is not None and embedding.embedding else None

    def store_embedding(
        self,
        *,
        organisationId: uuid.UUID,
        observationId: uuid.UUID,
        inputHash: str,
        embedding: tuple[float, ...],
    ) -> CorrelationEmbedding:
        """Insert a vector, or reuse the row when the input has not changed."""
        existing = self._session.scalar(
            select(CorrelationEmbedding).where(
                CorrelationEmbedding.observationId == observationId,
                CorrelationEmbedding.modelVersion == VECTOR_MODEL_VERSION,
                CorrelationEmbedding.inputHash == inputHash,
            )
        )
        if existing is not None:
            return existing
        row = CorrelationEmbedding(
            organisationId=organisationId,
            observationId=observationId,
            modelVersion=VECTOR_MODEL_VERSION,
            inputHash=inputHash,
            embedding=list(embedding),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def semantic_candidate_ids(
        self, subject: Observation, *, limit: int = MAX_CANDIDATES
    ) -> set[uuid.UUID]:
        """Nearest stored vectors in the same organisation, bounded by `limit`.

        `shortcut: only PostgreSQL has pgvector. SQLite keeps the existing
        time/space retrieval and the labelled keyword fallback.`
        """
        if self.dialect_name != "postgresql":
            return set()
        rows = self._session.execute(
            text(
                """
                SELECT candidate.observation_id
                FROM correlation_embeddings AS subject
                JOIN correlation_embeddings AS candidate
                  ON candidate.model_version = subject.model_version
                JOIN observations AS observation
                  ON observation.id = candidate.observation_id
                WHERE subject.observation_id = :subjectId
                  AND subject.model_version = :modelVersion
                  AND candidate.observation_id <> :subjectId
                  AND observation.organisation_id = :organisationId
                  AND observation.is_hidden IS FALSE
                ORDER BY subject.embedding <=> candidate.embedding
                LIMIT :candidateLimit
                """
            ),
            {
                "subjectId": subject.id,
                "modelVersion": VECTOR_MODEL_VERSION,
                "organisationId": subject.organisationId,
                "candidateLimit": limit,
            },
        )
        return set(rows.scalars().all())

    def candidate_rows(
        self,
        subject: Observation,
        *,
        limit: int = MAX_CANDIDATES,
        policy: RetrievalPolicy | None = None,
        semanticIds: set[uuid.UUID] | None = None,
    ) -> list[tuple[Observation, Any]]:
        """Return bounded candidates for `subject` as (observation, location WKT).

        Organisation scoping and the hidden flag are applied here, so a caller
        cannot accidentally retrieve across tenants. The bounds come from the
        subject's category, and tighten when it has no point to measure from.
        When semantic ids are supplied they narrow the set further; they never
        widen or bypass the existing bounds.
        """
        subjectPoint = parse_point_wkt(self.location_wkt(subject.id))
        bounds = policy or policy_for(
            subject.observationType, has_location=subjectPoint is not None
        )

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
            window = timedelta(hours=bounds.window_hours)
            statement = statement.where(
                Observation.observedAt.is_not(None),
                Observation.observedAt >= subjectObservedAt - window,
                Observation.observedAt <= subjectObservedAt + window,
            )

        # Push the distance test into PostgreSQL so the N nearest-by-time rows
        # are not first fetched only to be thrown away.
        indexedDistance = subjectPoint is not None and self.dialect_name == "postgresql"
        if indexedDistance:
            # parse_point_wkt returns (longitude, latitude), which is the order
            # format_point_wkt expects -- the reverse of the haversine call below.
            point = format_point_wkt(subjectPoint[0], subjectPoint[1])
            statement = statement.where(
                func.ST_DWithin(
                    Observation.location,
                    func.ST_GeogFromText(point),
                    bounds.radius_km * 1000.0,
                )
            )

        if semanticIds is not None:
            statement = statement.where(Observation.id.in_(semanticIds))

        statement = statement.order_by(Observation.receivedAt.desc()).limit(limit)

        rows: list[tuple[Observation, Any]] = []
        for row in self._session.execute(statement).all():
            candidate, candidateWkt = row[0], row[1]
            if not indexedDistance and subjectPoint is not None and candidateWkt is not None:
                point = parse_point_wkt(candidateWkt)
                if point is not None:
                    distance = haversine_km(
                        subjectPoint[1], subjectPoint[0], point[1], point[0]
                    )
                    if distance > bounds.radius_km:
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
        self, firstId: uuid.UUID, secondId: uuid.UUID
    ) -> EvidenceRelationship | None:
        """Find the row for a pair, whatever task it was stored under.

        Looking up by `(pair, task)` let one pair acquire a second row when the
        detector's verdict changed -- a source reference arriving after the first
        scan turns a `duplicate` into a `source_dependency`, and the reviewer saw
        both. The pair is the identity; the task is a field of it.
        """
        aId, bId = canonical_pair(firstId, secondId)
        return self._session.scalar(
            select(EvidenceRelationship)
            .where(
                EvidenceRelationship.observationAId == aId,
                EvidenceRelationship.observationBId == bId,
            )
            .order_by(EvidenceRelationship.task, EvidenceRelationship.createdAt)
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
        ambiguous: bool = False,
        methodVersion: str = METHOD_VERSION,
    ) -> EvidenceRelationship:
        """Insert a suggestion, or refresh and reclassify an undecided one.

        A decided row is never touched, whatever task it was decided under.
        """
        aId, bId = canonical_pair(firstId, secondId)
        existing = self.find_pair(aId, bId)
        if existing is not None:
            if existing.status != RelationshipStatus.SUGGESTED.value:
                return existing
            # The detector may now know more than it did (a source reference, a
            # corrected description). Reclassify in place rather than queueing
            # the same pair twice under two task names.
            existing.task = task
            existing.score = score
            existing.components = components
            existing.missingSignals = missingSignals
            existing.reasons = reasons
            existing.sourceIndependent = sourceIndependent
            existing.ambiguous = ambiguous
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
            ambiguous=ambiguous,
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

    def ensure_cluster(self, organisationId: uuid.UUID, observationId: uuid.UUID) -> uuid.UUID:
        """Return the cluster holding `observationId`, creating one if needed.

        Creating a cluster claims nothing: it gives a reviewer a place to look.
        An existing membership is left alone, which is what keeps a scan from
        joining A to C because both matched B.
        """
        existing = self._session.scalar(
            select(CorrelationClusterMember.clusterId).where(
                CorrelationClusterMember.observationId == observationId
            )
        )
        if existing is not None:
            return existing

        cluster = CorrelationCluster(organisationId=organisationId)
        self._session.add(cluster)
        self._session.flush()
        self._session.add(
            CorrelationClusterMember(clusterId=cluster.id, observationId=observationId)
        )
        self._session.flush()
        return cluster.id

    def clusters_with_members(
        self, organisationIds: set[uuid.UUID]
    ) -> list[tuple[CorrelationCluster, list[uuid.UUID]]]:
        """Clusters for the caller's organisations, with their observation ids."""
        if not organisationIds:
            return []
        clusters = list(
            self._session.scalars(
                select(CorrelationCluster)
                .where(CorrelationCluster.organisationId.in_(organisationIds))
                .order_by(CorrelationCluster.createdAt.desc())
            ).all()
        )
        members: dict[uuid.UUID, list[uuid.UUID]] = {cluster.id: [] for cluster in clusters}
        if clusters:
            for clusterId, observationId in self._session.execute(
                select(
                    CorrelationClusterMember.clusterId, CorrelationClusterMember.observationId
                ).where(CorrelationClusterMember.clusterId.in_(members))
            ).all():
                members[clusterId].append(observationId)
        return [(cluster, members[cluster.id]) for cluster in clusters]

    def count_for_task(self, task: CorrelationTask) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(EvidenceRelationship)
                .where(EvidenceRelationship.task == task.value)
            )
            or 0
        )

