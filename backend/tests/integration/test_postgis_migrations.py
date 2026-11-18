"""Live PostgreSQL + PostGIS migration, spatial, and SKIP LOCKED integration tests."""

import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.modules.jobs.models import JobStatus, ProcessingJob
from ecowatch.modules.jobs.repository import JobsRepository

pytestmark = pytest.mark.postgis


@pytest.mark.skipif(
    os.environ.get("ECOWATCH_RUN_POSTGIS_TESTS") != "1",
    reason="Set ECOWATCH_RUN_POSTGIS_TESTS=1 with running Postgres/PostGIS to verify migrations",
)
def test_alembic_upgrade_downgrade_and_skip_locked(tmp_path: Path) -> None:
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
            postgisVer = session.execute(text("SELECT postgis_version()")).scalar_one()
            assert postgisVer is not None

            # ADR-030: migration 0005 provisions pgvector in the same database.
            extensions = set(
                session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname IN ('postgis','vector')")
                ).scalars()
            )
            assert {"postgis", "vector"} <= extensions

            job = ProcessingJob(
                jobType="test.noop",
                payload={"temp": str(uuid.uuid4())},
                status=JobStatus.PENDING.value,
            )
            session.add(job)
            session.commit()

            claimed = JobsRepository(session).claim_next_batch(1)
            assert len(claimed) == 1
            assert claimed[0].id == job.id
            session.delete(claimed[0])
            session.commit()
    finally:
        command.downgrade(alembicCfg, "base")
        command.upgrade(alembicCfg, "head")
        engine.dispose()
        LocalFilesystemStorage(tmp_path / "storage")
        Settings(databaseUrl=dbUrl)
