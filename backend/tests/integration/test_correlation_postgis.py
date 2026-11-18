"""Live PostgreSQL checks for the Phase 2 correlation constraints.

SQLite cannot prove these: canonical pair ordering relies on PostgreSQL `uuid`
comparison, and the pair guarantee only means something if the constraints and
indexes actually exist in the schema.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ecowatch.modules.correlation.models import EvidenceRelationship
from ecowatch.modules.identity.models import Organisation
from ecowatch.modules.observations.models import Observation

pytestmark = pytest.mark.postgis


@pytest.mark.skipif(
    os.environ.get("ECOWATCH_RUN_POSTGIS_TESTS") != "1",
    reason="Set ECOWATCH_RUN_POSTGIS_TESTS=1 with running Postgres/PostGIS",
)
def test_correlation_constraints_and_indexes(tmp_path: Path) -> None:
    dbUrl = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://ecowatch:ecowatch_dev@localhost:5433/ecowatch",
    )
    backendDir = Path(__file__).resolve().parents[2]
    alembicCfg = Config(str(backendDir / "alembic.ini"))
    alembicCfg.set_main_option("script_location", str(backendDir / "alembic"))
    os.environ["DATABASE_URL"] = dbUrl
    command.upgrade(alembicCfg, "head")

    engine = create_engine(dbUrl)
    try:
        with Session(engine) as session:
            # Only Phase 2 objects are asserted: the constraints and indexes
            # correlation relies on for correctness at scale.
            constraints = set(
                session.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'evidence_relationships'::regclass"
                    )
                ).scalars()
            )
            assert "uq_evidence_relationships_pair_task" in constraints
            assert "ck_evidence_relationships_ordered" in constraints
            assert "ck_evidence_relationships_distinct" in constraints

            indexes = set(
                session.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE tablename = 'evidence_relationships'"
                    )
                ).scalars()
            )
            assert "ix_evidence_relationships_observation_b_id" in indexes
            assert "ix_evidence_relationships_status" in indexes
            assert "ix_observations_source_ref" in set(
                session.execute(
                    text("SELECT indexname FROM pg_indexes WHERE tablename = 'observations'")
                ).scalars()
            )

            org = Organisation(
                name=f"Correlation Constraints {uuid.uuid4().hex[:8]}", orgType="ngo"
            )
            session.add(org)
            session.flush()
            first, second = _two_observations(session, org)
            session.commit()

            lowId, highId = sorted((first.id, second.id))

            # Unordered pair: the check constraint must refuse it rather than
            # store the same pair twice with the ends swapped.
            session.add(_relationship(org, highId, lowId))
            with pytest.raises(IntegrityError):
                session.flush()
            session.rollback()

            session.add(_relationship(org, lowId, highId))
            session.commit()

            session.add(_relationship(org, lowId, highId))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            assert session.query(EvidenceRelationship).count() == 1
    finally:
        command.downgrade(alembicCfg, "base")
        command.upgrade(alembicCfg, "head")
        engine.dispose()


def _two_observations(session: Session, org: Organisation) -> tuple[Observation, Observation]:
    observations = []
    for _ in range(2):
        observation = Observation(
            organisationId=org.id,
            idempotencyKey=uuid.uuid4(),
            payloadHash="0" * 64,
            observationType="water_pollution",
            sourceType="community_registered",
            description="dead fish at the river bend",
            observedAt=datetime.now(UTC) - timedelta(hours=2),
            receivedAt=datetime.now(UTC),
            timePrecision="exact",
            locationPrecision="unknown",
            qualityFlags=[],
            accessClass="internal",
            currentVersion=1,
        )
        session.add(observation)
        observations.append(observation)
    session.flush()
    return observations[0], observations[1]


def _relationship(org: Organisation, aId: uuid.UUID, bId: uuid.UUID) -> EvidenceRelationship:
    return EvidenceRelationship(
        organisationId=org.id,
        observationAId=aId,
        observationBId=bId,
        task="same_event",
        score=0.5,
        components={},
        missingSignals=[],
        reasons=[],
        methodVersion="correlation-1",
        sourceIndependent=True,
        status="suggested",
    )


@pytest.mark.skipif(
    os.environ.get("ECOWATCH_RUN_POSTGIS_TESTS") != "1",
    reason="Set ECOWATCH_RUN_POSTGIS_TESTS=1 with running Postgres/PostGIS",
)
def test_distance_is_filtered_by_postgis_not_by_python() -> None:
    """ST_DWithin on geography, so the GiST index is what bounds the scan."""
    dbUrl = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://ecowatch:ecowatch_dev@localhost:5433/ecowatch",
    )
    backendDir = Path(__file__).resolve().parents[2]
    alembicCfg = Config(str(backendDir / "alembic.ini"))
    alembicCfg.set_main_option("script_location", str(backendDir / "alembic"))
    os.environ["DATABASE_URL"] = dbUrl
    command.upgrade(alembicCfg, "head")

    engine = create_engine(dbUrl)
    try:
        with Session(engine) as session:
            indexes = set(
                session.execute(
                    text("SELECT indexname FROM pg_indexes WHERE tablename = 'observations'")
                ).scalars()
            )
            assert "ix_observations_location_gist" in indexes, (
                "the GiST index ST_DWithin relies on is missing"
            )

            org = Organisation(
                name=f"Correlation Distance {uuid.uuid4().hex[:8]}", orgType="ngo"
            )
            session.add(org)
            session.flush()

            # Same wording and time for all three, so distance is the only
            # signal that can separate them.
            observedAt = datetime.now(UTC) - timedelta(hours=2)
            subject = _located_observation(session, org, 6.6885, -1.6244, observedAt)
            _located_observation(session, org, 6.6950, -1.6250, observedAt)  # ~0.7 km
            _located_observation(session, org, 7.9500, -1.0300, observedAt)  # ~200 km
            session.commit()

            from ecowatch.modules.correlation.service import CorrelationService

            assert CorrelationService(session).scan_observation(subject.id) == 1
            suggestion = session.query(EvidenceRelationship).one()
            partners = {suggestion.observationAId, suggestion.observationBId} - {subject.id}
            assert len(partners) == 1
            assert "spatial_proximity" in suggestion.components
    finally:
        command.downgrade(alembicCfg, "base")
        command.upgrade(alembicCfg, "head")
        engine.dispose()


def _located_observation(
    session: Session,
    org: Organisation,
    latitude: float,
    longitude: float,
    observedAt: datetime,
) -> Observation:
    from ecowatch.core.spatial import format_point_wkt

    observation = Observation(
        organisationId=org.id,
        idempotencyKey=uuid.uuid4(),
        payloadHash="0" * 64,
        observationType="water_pollution",
        sourceType="community_registered",
        description="oily sheen at the river bend",
        observedAt=observedAt,
        receivedAt=datetime.now(UTC),
        timePrecision="exact",
        location=format_point_wkt(longitude, latitude),
        locationPrecision="exact",
        qualityFlags=[],
        accessClass="internal",
        currentVersion=1,
    )
    session.add(observation)
    session.flush()
    return observation
