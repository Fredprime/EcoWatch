"""Alembic migration environment importing all Phase 1 ORM models."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ecowatch.core.config import get_settings
from ecowatch.core.models import Base
from ecowatch.core.rate_limit import RateLimitBucket  # noqa: F401
from ecowatch.modules.audit.models import AuditEvent  # noqa: F401
from ecowatch.modules.cases.models import Case, CaseObservation  # noqa: F401
from ecowatch.modules.evidence.models import AssetDerivative, EvidenceAsset  # noqa: F401
from ecowatch.modules.identity.models import Membership, Organisation, User  # noqa: F401
from ecowatch.modules.jobs.models import ProcessingJob  # noqa: F401
from ecowatch.modules.notifications.models import ClarificationRequest, Notification  # noqa: F401
from ecowatch.modules.observations.models import (  # noqa: F401
    Method,
    Observation,
    ObservationSource,
    ObservationVersion,
    Unit,
)

alembicConfig = context.config

if alembicConfig.config_file_name is not None:
    fileConfig(alembicConfig.config_file_name)

targetMetadata = Base.metadata


def get_url() -> str:
    """Resolve database URL from environment/settings rather than static ini."""
    return get_settings().databaseUrl


def run_migrations_offline() -> None:
    """Run migrations in offline SQL generation mode."""
    context.configure(
        url=get_url(),
        target_metadata=targetMetadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    section = alembicConfig.get_section(alembicConfig.config_ini_section, {})
    section["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=targetMetadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
