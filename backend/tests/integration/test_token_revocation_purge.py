"""Integration tests for the bounded, admin-only expired revoked-token purge.

All records are temporary and live in the isolated per-test database.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.identity.models import RevokedToken
from ecowatch.modules.identity.permissions import SystemRole
from tests.conftest import auth_headers, create_temp_user

PURGE_PATH = "/api/v1/auth/revoked-tokens/purge"


def _seed_revocations(
    dbSession: Session, userId: uuid.UUID, *, expired: int, active: int
) -> datetime:
    """Add temporary expired and still-valid revocation rows; return the reference time."""
    now = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
    for index in range(expired):
        dbSession.add(
            RevokedToken(
                tokenId=uuid.uuid4(),
                userId=userId,
                expiresAt=now - timedelta(days=index + 1),
            )
        )
    for index in range(active):
        dbSession.add(
            RevokedToken(
                tokenId=uuid.uuid4(),
                userId=userId,
                expiresAt=now + timedelta(days=index + 1),
            )
        )
    dbSession.commit()
    return now


def _row_count(dbSession: Session) -> int:
    return int(dbSession.scalar(select(func.count()).select_from(RevokedToken)) or 0)


def _purge_event_counts(dbSession: Session) -> list[int]:
    rows = dbSession.scalars(
        select(AuditEvent).where(AuditEvent.action == "auth.revoked_tokens_purged")
    ).all()
    return sorted(int(event.details["deletedCount"]) for event in rows)


def test_system_admin_purges_only_expired_rows_in_bounded_batches(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    admin = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    headers = auth_headers(authProvider, admin)
    cutoff = _seed_revocations(dbSession, admin.id, expired=3, active=2)

    first = client.post(PURGE_PATH, headers=headers, params={"limit": 2})
    assert first.status_code == 200, first.text
    assert first.json() == {"deletedCount": 2}
    assert _row_count(dbSession) == 3

    second = client.post(PURGE_PATH, headers=headers, params={"limit": 2})
    assert second.status_code == 200, second.text
    assert second.json() == {"deletedCount": 1}

    third = client.post(PURGE_PATH, headers=headers)
    assert third.status_code == 200, third.text
    assert third.json() == {"deletedCount": 0}
    assert _row_count(dbSession) == 2
    # SQLite drops tzinfo on read; compare in the same naive form.
    naiveCutoff = cutoff.replace(tzinfo=None)
    assert all(
        expiresAt > naiveCutoff
        for expiresAt in dbSession.scalars(select(RevokedToken.expiresAt)).all()
    )

    assert _purge_event_counts(dbSession) == [0, 1, 2]
    events = dbSession.scalars(
        select(AuditEvent).where(AuditEvent.action == "auth.revoked_tokens_purged")
    ).all()
    assert all(event.actorUserId == admin.id for event in events)
    assert all(event.actorRole == "system_admin" for event in events)


def test_non_admin_and_anonymous_cannot_purge(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    reviewer = create_temp_user(dbSession)
    _seed_revocations(dbSession, reviewer.id, expired=2, active=1)

    denied = client.post(PURGE_PATH, headers=auth_headers(authProvider, reviewer))
    assert denied.status_code == 403, denied.text
    assert denied.json()["code"] == "FORBIDDEN"

    anonymous = client.post(PURGE_PATH)
    assert anonymous.status_code == 401, anonymous.text
    assert _row_count(dbSession) == 3
    assert dbSession.scalar(select(func.count()).select_from(AuditEvent)) == 0

    admin = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    adminHeaders = auth_headers(authProvider, admin)
    assert client.post(PURGE_PATH, headers=adminHeaders, params={"limit": 0}).status_code == 422
    assert client.post(PURGE_PATH, headers=adminHeaders, params={"limit": 501}).status_code == 422
