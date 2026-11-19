"""Password hashing, tracking-code hashing, and swappable AuthProvider interface."""

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Protocol


def hash_password(password: str, *, iterations: int = 210_000) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return (
        f"pbkdf2_sha256${iterations}$"
        f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, storedHash: str) -> bool:
    """Constant-time verification of a PBKDF2-HMAC-SHA256 password hash."""
    try:
        scheme, iterStr, saltB64, digestB64 = storedHash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterStr)
        salt = base64.urlsafe_b64decode(saltB64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digestB64.encode("ascii"))
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def generate_tracking_code() -> str:
    """Generate a high-entropy (>=128-bit) anonymous receipt tracking code."""
    return secrets.token_urlsafe(24)


def hash_tracking_code(code: str, secret: str) -> str:
    """Hash a tracking code with HMAC-SHA256 for storage at rest."""
    return hmac.new(secret.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Verified bearer token claims."""

    userId: uuid.UUID
    issuedAt: int
    expiresAt: int
    tokenId: uuid.UUID | None = None


class AuthProvider(Protocol):
    """Provider boundary so local token auth can swap to OIDC/IdP later."""

    def issue_token(self, userId: uuid.UUID) -> str: ...
    def verify_token(self, token: str) -> TokenClaims | None: ...


class LocalTokenAuthProvider:
    """Stateless HMAC-SHA256 signed bearer token provider for Phase 1 auth."""

    def __init__(self, secret: str, ttlSeconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._ttlSeconds = ttlSeconds

    def issue_token(self, userId: uuid.UUID) -> str:
        now = int(time.time())
        payload = {
            "sub": str(userId),
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + self._ttlSeconds,
        }
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        sig = hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).hexdigest()
        return f"{encoded}.{sig}"

    def verify_token(self, token: str) -> TokenClaims | None:
        try:
            encoded, sig = token.split(".", 1)
        except ValueError:
            return None
        expectedSig = hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expectedSig):
            return None
        try:
            payload = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8"))
            userId = uuid.UUID(payload["sub"])
            iat = int(payload["iat"])
            exp = int(payload["exp"])
            rawJti = payload.get("jti")
            tokenId = uuid.UUID(rawJti) if rawJti is not None else None
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None
        if exp < int(time.time()):
            return None
        return TokenClaims(userId=userId, issuedAt=iat, expiresAt=exp, tokenId=tokenId)
