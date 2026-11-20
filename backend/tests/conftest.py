"""Shared pytest fixtures for EcoWatch Phase 1 unit, API, security, and PostGIS tests."""

import io
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ecowatch.api.dependencies import get_auth_provider, get_storage
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_db
from ecowatch.core.models import Base
from ecowatch.core.rate_limit import RateLimitBucket  # noqa: F401
from ecowatch.core.security import LocalTokenAuthProvider, hash_password
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.main import create_app
from ecowatch.modules.audit.models import AuditEvent  # noqa: F401
from ecowatch.modules.cases.models import Case, CaseObservation  # noqa: F401
from ecowatch.modules.catalogue.models import Dataset, DatasetVersion
from ecowatch.modules.correlation.models import (  # noqa: F401
    EvidenceRelationship,
)
from ecowatch.modules.evidence.models import AssetDerivative, EvidenceAsset  # noqa: F401
from ecowatch.modules.identity.models import Membership, Organisation, User
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.jobs.models import ProcessingJob  # noqa: F401
from ecowatch.modules.notifications.models import ClarificationRequest, Notification  # noqa: F401
from ecowatch.modules.observations.models import (  # noqa: F401
    Method,
    Observation,
    ObservationSource,
    ObservationVersion,
    Unit,
)


@pytest.fixture()
def testSettings(tmp_path: Path) -> Settings:
    """Isolated settings pointing to a temporary directory and test secret."""
    return Settings(
        appName="EcoWatch Test API",
        environment="test",
        databaseUrl="sqlite+pysqlite:///:memory:",
        authSecret="test-secret-key-for-ecowatch-phase1",
        authTokenTtlSeconds=3600,
        storageRoot=tmp_path / "storage",
        maxUploadBytes=1024 * 1024,
        publicIntakeRateLimit=50,
        publicIntakeWindowSeconds=60,
        trackingLookupMaxAttempts=3,
        trackingLookupLockoutSeconds=300,
        workerEnabled=False,
    )


@pytest.fixture()
def dbSessionFactory() -> Generator[sessionmaker[Session]]:
    """Fresh in-memory SQLite engine & schema per test (disposed after test)."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def dbSession(dbSessionFactory: sessionmaker[Session]) -> Generator[Session]:
    """Yield a temporary SQLAlchemy session cleaned up at teardown."""
    session = dbSessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def storageProvider(testSettings: Settings) -> LocalFilesystemStorage:
    """Temporary filesystem storage outside any repo directory."""
    return LocalFilesystemStorage(testSettings.storageRoot)


@pytest.fixture()
def authProvider(testSettings: Settings) -> LocalTokenAuthProvider:
    """Token provider bound to testSettings."""
    return LocalTokenAuthProvider(testSettings.authSecret, testSettings.authTokenTtlSeconds)


@pytest.fixture()
def app(
    testSettings: Settings,
    dbSessionFactory: sessionmaker[Session],
    storageProvider: LocalFilesystemStorage,
    authProvider: LocalTokenAuthProvider,
) -> FastAPI:
    """FastAPI app wired to isolated temporary DB, storage, and auth dependencies."""
    application = create_app(testSettings)

    def overrideDb() -> Generator[Session]:
        session = dbSessionFactory()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db] = overrideDb
    application.dependency_overrides[get_settings] = lambda: testSettings
    application.dependency_overrides[get_storage] = lambda: storageProvider
    application.dependency_overrides[get_auth_provider] = lambda: authProvider
    return application


@pytest.fixture()
def client(app: FastAPI) -> Generator[TestClient]:
    """FastAPI TestClient scoped to one isolated test."""
    with TestClient(app) as testClient:
        yield testClient


def create_temp_org(dbSession: Session, *, name: str | None = None) -> Organisation:
    """Create a temporary organisation record for testing."""
    org = Organisation(
        name=name or f"Temp Org {uuid.uuid4().hex[:8]}",
        orgType="ngo",
        isActive=True,
    )
    dbSession.add(org)
    dbSession.commit()
    return org


def create_temp_user(
    dbSession: Session,
    *,
    email: str | None = None,
    password: str = "Passw0rd!Test",
    systemRole: SystemRole | None = None,
    memberships: list[tuple[uuid.UUID, Role]] | None = None,
) -> User:
    """Create a temporary user and optional organisation memberships for testing."""
    user = User(
        email=email or f"user-{uuid.uuid4().hex[:8]}@example.test",
        displayName="Test User",
        passwordHash=hash_password(password),
        systemRole=systemRole.value if systemRole else None,
        isActive=True,
    )
    dbSession.add(user)
    dbSession.flush()
    for orgId, role in memberships or []:
        dbSession.add(
            Membership(userId=user.id, organisationId=orgId, role=role.value, isActive=True)
        )
    dbSession.commit()
    return user


def auth_headers(authProvider: LocalTokenAuthProvider, user: User) -> dict[str, str]:
    """Build Authorization bearer header for a temporary test user."""
    token = authProvider.issue_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def make_stored_dataset_version(
    dbSession: Session,
    storageProvider: LocalFilesystemStorage,
    organisationId: uuid.UUID,
) -> uuid.UUID:
    """Create a real dataset version with tiny stored CSV for analysis execution tests."""
    dataset = Dataset(
        organisationId=organisationId,
        name=f"ds-{uuid.uuid4().hex[:8]}",
        owner="EcoWatch",
        licence="CC-BY-4.0",
        attribution="EcoWatch",
        permittedUse="Monitoring",
        crs="EPSG:4326",
    )
    dbSession.add(dataset)
    dbSession.flush()
    key = f"datasets/{uuid.uuid4().hex}.csv"
    version = DatasetVersion(
        datasetId=dataset.id,
        versionLabel="v1",
        sourceAcquisitionAt=datetime(2026, 11, 19, 9, 0, tzinfo=UTC),
        resolution="10m",
        crs="EPSG:4326",
        method="Field sampling",
        licenceSnapshot="CC-BY-4.0",
        attributionSnapshot="EcoWatch",
        permittedUseSnapshot="Monitoring",
        storageKey=key,
    )
    dbSession.add(version)
    dbSession.flush()
    storageProvider.put_bytes(key, b"site,reading\nA,1.5\nB,2.5\n")
    dbSession.commit()
    return version.id


def make_jpeg_with_exif_bytes() -> bytes:
    """Generate a tiny in-memory JPEG image carrying synthetic EXIF GPS/software metadata."""
    image = Image.new("RGB", (32, 32), color=(40, 120, 60))
    exif = Image.Exif()
    exif[0x0131] = "TestCamera 1.0"  # Software tag
    exif[0x010F] = "EcoCamera"  # Make tag
    buf = io.BytesIO()
    image.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()
