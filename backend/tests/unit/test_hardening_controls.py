"""Unit and API tests for backend hardening, limits, caching, compression, N+1, and metrics."""

import asyncio
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

from ecowatch.api.dependencies import get_auth_provider, get_storage
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import build_engine, get_db
from ecowatch.core.middleware import RequestLimitsAndHeadersMiddleware
from ecowatch.core.security import LocalTokenAuthProvider, hash_password
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.main import create_app
from ecowatch.modules.evidence.models import AssetDerivative, DerivativeType, EvidenceAsset
from ecowatch.modules.evidence.service import EvidenceService
from ecowatch.modules.identity.models import Membership, Organisation, User
from ecowatch.modules.identity.permissions import Principal, Role, SystemRole
from ecowatch.modules.observations.models import (
    AccessClass,
    Observation,
    ObservationSource,
    ObservationVersion,
    SourceType,
)
from ecowatch.modules.observations.service import ObservationService


def _build_custom_client(
    settings: Settings, dbSessionFactory: sessionmaker[Session]
) -> TestClient:
    app = create_app(settingsOverride=settings)

    def _override_db():
        session = dbSessionFactory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_storage] = lambda: LocalFilesystemStorage(settings.storageRoot)
    app.dependency_overrides[get_auth_provider] = lambda: LocalTokenAuthProvider(
        settings.authSecret, settings.authTokenTtlSeconds
    )
    return TestClient(app)


def test_postgres_engine_configures_pool_and_statement_timeout() -> None:
    cfg = Settings(
        databaseUrl="postgresql+psycopg://user:pass@localhost:5433/ecowatch",
        dbPoolSize=7,
        dbMaxOverflow=3,
        dbPoolTimeoutSeconds=12,
        dbPoolRecycleSeconds=900,
        dbStatementTimeoutMs=8000,
    )
    engine = build_engine(cfg)
    try:
        assert engine.pool.size() == 7
        assert engine.pool._max_overflow == 3
        assert engine.pool._timeout == 12
        assert engine.pool._recycle == 900
    finally:
        engine.dispose()


def test_request_size_limit_rejects_oversized_json_body(
    testSettings: Settings, dbSessionFactory: sessionmaker[Session]
) -> None:
    tight = testSettings.model_copy(update={"maxJsonBodyBytes": 1024})
    with _build_custom_client(tight, dbSessionFactory) as client:
        resp = client.post(
            "/api/v1/auth/login",
            content=b'{"email":"a@b.com","password":"' + b"x" * 2000 + b'"}',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 413
        body = resp.json()
        assert body["code"] == "PAYLOAD_TOO_LARGE"
        assert resp.headers["Cache-Control"] == "no-store, private"


def test_request_timeout_and_concurrency_limits(testSettings: Settings) -> None:
    miniApp = FastAPI()
    tight = testSettings.model_copy(
        update={"requestTimeoutSeconds": 1.0, "maxConcurrentRequests": 1}
    )
    miniApp.add_middleware(RequestLimitsAndHeadersMiddleware, settings=tight)

    @miniApp.get("/slow")
    async def slow_route() -> dict[str, str]:
        await asyncio.sleep(1.5)
        return {"ok": "late"}

    with TestClient(miniApp) as client:
        resp = client.get("/slow")
        assert resp.status_code == 504
        assert resp.json()["category"] == "transient"
        assert resp.headers["Retry-After"] == "5"


def test_cache_control_isolation_and_gzip_and_metrics(
    client: TestClient, dbSession: Session, authProvider: LocalTokenAuthProvider
) -> None:
    user = User(
        email="cache_user@ecowatch.test",
        displayName="Cache User",
        passwordHash=hash_password("StrongPass123!"),
        systemRole=SystemRole.SYSTEM_ADMIN.value,
        isActive=True,
    )
    dbSession.add(user)
    dbSession.commit()
    authHeaders = {"Authorization": f"Bearer {authProvider.issue_token(user.id)}"}

    # Public unauthenticated cacheable endpoint
    pubResp = client.get("/api/v1/public/cases")
    assert pubResp.status_code == 200
    assert pubResp.headers["Cache-Control"] == "public, max-age=30"
    assert pubResp.headers["X-Content-Type-Options"] == "nosniff"

    # Authenticated request to same or private endpoint MUST NOT be publicly cached
    privPublicResp = client.get("/api/v1/public/cases", headers=authHeaders)
    assert privPublicResp.status_code == 200
    assert privPublicResp.headers["Cache-Control"] == "no-store, private"
    assert "Authorization" in privPublicResp.headers["Vary"]

    meResp = client.get("/api/v1/auth/me", headers=authHeaders)
    assert meResp.status_code == 200
    assert meResp.headers["Cache-Control"] == "no-store, private"

    # Metrics endpoint returns Prometheus text with no-store and no PII/secrets
    metricsResp = client.get("/metrics")
    assert metricsResp.status_code == 200
    assert "ecowatch_http_requests_total" in metricsResp.text
    assert "ecowatch_active_requests" in metricsResp.text
    assert metricsResp.headers["Cache-Control"] == "no-store, private"
    assert "test-secret" not in metricsResp.text


def test_gzip_compression_on_large_response(
    testSettings: Settings, dbSessionFactory: sessionmaker[Session]
) -> None:
    tight = testSettings.model_copy(update={"gzipMinimumSize": 100})
    with _build_custom_client(tight, dbSessionFactory) as client:
        resp = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
        assert resp.status_code == 200
        assert resp.headers.get("content-encoding") == "gzip"


def test_public_cases_and_export_rate_limiting(
    testSettings: Settings, dbSessionFactory: sessionmaker[Session]
) -> None:
    tight = testSettings.model_copy(
        update={
            "publicApiBurstLimit": 2,
            "publicApiBurstWindowSeconds": 60,
            "expensiveEndpointRateLimit": 1,
            "expensiveEndpointWindowSeconds": 60,
        }
    )
    with dbSessionFactory() as db:
        org = Organisation(name="RL Org", orgType="NGO", isActive=True)
        db.add(org)
        db.flush()
        admin = User(
            email="rl_admin@ecowatch.test",
            displayName="RL Admin",
            passwordHash=hash_password("StrongPass123!"),
            systemRole=SystemRole.SYSTEM_ADMIN.value,
            isActive=True,
        )
        db.add(admin)
        db.flush()
        db.add(
            Membership(
                userId=admin.id,
                organisationId=org.id,
                role=Role.ORGANISATION_ADMIN.value,
                isActive=True,
            )
        )
        db.commit()
        orgId = org.id
        adminId = admin.id

    token = LocalTokenAuthProvider(tight.authSecret, 3600).issue_token(adminId)
    headers = {"Authorization": f"Bearer {token}"}

    with _build_custom_client(tight, dbSessionFactory) as client:
        assert client.get("/api/v1/public/cases").status_code == 200
        assert client.get("/api/v1/public/cases").status_code == 200
        limited = client.get("/api/v1/public/cases")
        assert limited.status_code == 429
        assert "Retry-After" in limited.headers

        exportOk = client.get(
            f"/api/v1/observations/export?organisationId={orgId}", headers=headers
        )
        assert exportOk.status_code == 200
        exportLimited = client.get(
            f"/api/v1/observations/export?organisationId={orgId}", headers=headers
        )
        assert exportLimited.status_code == 429


def test_n_plus_one_eliminated_for_evidence_list_and_obs_export(
    dbSession: Session, storageProvider: LocalFilesystemStorage
) -> None:
    org = Organisation(name="Batch Org", orgType="NGO", isActive=True)
    dbSession.add(org)
    dbSession.flush()
    user = User(
        email="batch@ecowatch.test",
        displayName="Batch User",
        passwordHash=hash_password("StrongPass123!"),
        systemRole=SystemRole.SYSTEM_ADMIN.value,
        isActive=True,
    )
    dbSession.add(user)
    dbSession.flush()
    principal = Principal(
        userId=user.id,
        systemRole=SystemRole.SYSTEM_ADMIN,
        isAuthenticated=True,
    )

    now = datetime.now(UTC)
    obsIds: list[uuid.UUID] = []
    for idx in range(6):
        obs = Observation(
            organisationId=org.id,
            idempotencyKey=uuid.uuid4(),
            payloadHash=f"{idx:064x}",
            submittedByUserId=user.id,
            sourceType=SourceType.FIELD_TEAM.value,
            observationType="water_discolouration",
            description=f"Obs {idx}",
            observedAt=now,
            submittedAt=now,
            receivedAt=now,
            timePrecision="exact",
            locationPrecision="exact",
            accessClass=AccessClass.RESTRICTED.value,
        )
        dbSession.add(obs)
        dbSession.flush()
        obsIds.append(obs.id)
        dbSession.add(
            ObservationVersion(
                observationId=obs.id,
                versionNumber=1,
                editedByUserId=user.id,
                changedFields={"description": f"Obs {idx}"},
                reason="initial",
                createdAt=now,
            )
        )
        dbSession.add(
            ObservationSource(
                observationId=obs.id,
                reporterName=f"Reporter {idx}",
                contactChannel="email",
                privacyNoticeVersion="v1",
            )
        )

    for idx in range(6):
        asset = EvidenceAsset(
            observationId=obsIds[0],
            organisationId=org.id,
            uploadedByUserId=user.id,
            originalFilename=f"img_{idx}.png",
            declaredMimeType="image/png",
            detectedMimeType="image/png",
            sizeBytes=128,
            sha256Checksum=f"{idx:064x}",
            storageKey=f"originals/test_{idx}.png",
            accessClass=AccessClass.RESTRICTED.value,
            receivedAt=now,
            createdAt=now,
        )
        dbSession.add(asset)
        dbSession.flush()
        dbSession.add(
            AssetDerivative(
                parentAssetId=asset.id,
                derivativeType=DerivativeType.THUMBNAIL.value,
                storageKey=f"derivatives/thumb_{idx}.png",
                mimeType="image/png",
                sizeBytes=64,
                sha256Checksum=f"{idx + 100:064x}",
                exifStripped=True,
                accessClass=AccessClass.INTERNAL.value,
                createdAt=now,
            )
        )
    dbSession.commit()

    queryCount = 0

    def _count_queries(*_args) -> None:
        nonlocal queryCount
        queryCount += 1

    engine = dbSession.get_bind()
    event.listen(engine, "before_cursor_execute", _count_queries)
    try:
        queryCount = 0
        assets = EvidenceService(dbSession, storageProvider).list_observation_evidence(
            principal, obsIds[0]
        )
        assert len(assets) == 6
        assert all(len(a.derivatives) == 1 for a in assets)
        # 1 obs lookup + 1 assets query + 1 batched derivatives IN(...) query = 3
        assert queryCount <= 3

        queryCount = 0
        exported = ObservationService(dbSession).export_observations(principal, org.id)
        assert len(exported.observations) == 6
        # 1 obs export list + 1 batched versions + 1 batched sources + 1 audit insert = 4
        assert queryCount <= 5
    finally:
        event.remove(engine, "before_cursor_execute", _count_queries)
