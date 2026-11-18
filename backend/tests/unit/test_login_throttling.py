"""Unit and API checks for login throttling and observation DTO privacy."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.rate_limit import RateLimitBucket
from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.identity.permissions import Role
from ecowatch.modules.identity.service import login_bucket_key
from tests.conftest import auth_headers, create_temp_org, create_temp_user


def _login(client: TestClient, password: str = "wrong-password") -> object:
    return client.post(
        "/api/v1/auth/login",
        json={"email": "throttle@example.test", "password": password},
    )


def test_failed_logins_are_throttled_and_bucket_has_no_plaintext_pii(
    client: TestClient,
    dbSession: Session,
    testSettings: Settings,
) -> None:
    testSettings.loginMaxAttempts = 2
    testSettings.loginWindowSeconds = 60
    testSettings.loginLockoutSeconds = 300
    create_temp_user(dbSession, email="throttle@example.test", password="Correct123!")

    assert _login(client).status_code == 401
    assert _login(client).status_code == 401
    locked = _login(client)
    assert locked.status_code == 429
    assert locked.json()["code"] == "RATE_LIMIT_EXCEEDED"

    bucket = dbSession.execute(select(RateLimitBucket)).scalar_one()
    assert bucket.bucketKey.startswith("login:")
    assert "throttle@example.test" not in bucket.bucketKey
    assert "testclient" not in bucket.bucketKey
    assert bucket.attemptCount == 3
    assert bucket.lockedUntil is not None

    assert login_bucket_key(" User@Example.test ", "ip-a") == login_bucket_key(
        "user@example.test", "ip-a"
    )
    assert login_bucket_key("user@example.test", "ip-a") != login_bucket_key(
        "user@example.test", "ip-b"
    )


def test_successful_login_resets_the_failure_bucket(
    client: TestClient,
    dbSession: Session,
    testSettings: Settings,
) -> None:
    testSettings.loginMaxAttempts = 2
    create_temp_user(dbSession, email="throttle@example.test", password="Correct123!")

    assert _login(client).status_code == 401
    assert _login(client, "Correct123!").status_code == 200
    assert dbSession.execute(select(RateLimitBucket)).scalar_one_or_none() is None

    assert _login(client).status_code == 401
    assert _login(client).status_code == 401
    assert _login(client).status_code == 429


def test_public_observation_dto_omits_raw_location_wording(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    org = create_temp_org(dbSession)
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    investigator = create_temp_user(dbSession, memberships=[(org.id, Role.INVESTIGATOR)])
    reviewerHeaders = auth_headers(authProvider, reviewer)
    investigatorHeaders = auth_headers(authProvider, investigator)

    created = client.post(
        "/api/v1/observations",
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "organisationId": str(org.id),
            "observationType": "water",
            "description": "Sheen on stream",
            "timePrecision": "approximate",
            "originalTimeWording": "recent days",
            "locationPrecision": "area",
            "originalLocationWording": "behind the borehole at Plot 7",
            "accessClass": "restricted",
        },
    )
    assert created.status_code == 201
    observationId = created.json()["observationId"]

    listed = client.get("/api/v1/observations", headers=reviewerHeaders)
    assert listed.status_code == 200
    assert listed.json()["items"]
    assert all("originalLocationWording" not in item for item in listed.json()["items"])

    publicDetail = client.get(f"/api/v1/observations/{observationId}", headers=reviewerHeaders)
    assert publicDetail.status_code == 200
    assert "originalLocationWording" not in publicDetail.json()

    restrictedDetail = client.get(
        f"/api/v1/observations/{observationId}", headers=investigatorHeaders
    )
    assert restrictedDetail.status_code == 200
    assert restrictedDetail.json()["originalLocationWording"] == "behind the borehole at Plot 7"
