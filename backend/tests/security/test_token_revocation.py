"""Security tests for server-side bearer token revocation on logout."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import hash_password
from ecowatch.modules.identity.models import User


def test_logout_revokes_token_server_side(
    client: TestClient, dbSession: Session
) -> None:
    user = User(
        email="logout_test@ecowatch.test",
        displayName="Logout User",
        passwordHash=hash_password("StrongPass123!"),
        isActive=True,
    )
    dbSession.add(user)
    dbSession.commit()

    loginResp = client.post(
        "/api/v1/auth/login",
        json={"email": "logout_test@ecowatch.test", "password": "StrongPass123!"},
    )
    assert loginResp.status_code == 200
    token1 = loginResp.json()["accessToken"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    assert client.get("/api/v1/auth/me", headers=headers1).status_code == 200

    logoutResp = client.post("/api/v1/auth/logout", headers=headers1)
    assert logoutResp.status_code == 200
    assert logoutResp.json() == {"revoked": True}

    # Revoked token is rejected immediately on subsequent requests
    assert client.get("/api/v1/auth/me", headers=headers1).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=headers1).status_code == 401

    # New login issues a fresh jti token that works
    loginResp2 = client.post(
        "/api/v1/auth/login",
        json={"email": "logout_test@ecowatch.test", "password": "StrongPass123!"},
    )
    assert loginResp2.status_code == 200
    token2 = loginResp2.json()["accessToken"]
    assert token2 != token1
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"}
        ).status_code
        == 200
    )
