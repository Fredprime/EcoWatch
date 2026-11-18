"""SQLAlchemy engine, connection pooling, and PostgreSQL/PostGIS health checks."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ecowatch.core.config import Settings, get_settings


def build_engine(settings: Settings | None = None) -> Engine:
    """Create a pooled SQLAlchemy engine for PostgreSQL/PostGIS."""
    cfg = settings or get_settings()
    engineKwargs: dict[str, object] = {"pool_pre_ping": True}
    if not cfg.databaseUrl.startswith("sqlite"):
        engineKwargs["pool_size"] = cfg.dbPoolSize
        engineKwargs["max_overflow"] = cfg.dbMaxOverflow
    return create_engine(cfg.databaseUrl, **engineKwargs)


_engine: Engine | None = None
_sessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Lazily create and return the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Lazily create and return the shared session factory."""
    global _sessionFactory
    if _sessionFactory is None:
        _sessionFactory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sessionFactory


def get_db() -> Generator[Session]:
    """FastAPI dependency yielding a scoped SQLAlchemy session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def check_database_readiness(session: Session) -> tuple[bool, str | None]:
    """Verify database connectivity and PostGIS availability when running on PostgreSQL."""
    session.execute(text("SELECT 1"))
    dialectName = session.bind.dialect.name if session.bind is not None else ""
    if dialectName == "postgresql":
        version = session.execute(text("SELECT postgis_version()")).scalar_one_or_none()
        return True, str(version) if version is not None else None
    return True, f"dialect:{dialectName}"
