"""Application configuration loaded natively from environment and .env files."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator


def _load_dotenv_values(envPath: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines from an optional .env file without extra dependencies."""
    if not envPath.is_file():
        return {}
    parsed: dict[str, str] = {}
    for rawLine in envPath.read_text(encoding="utf-8").splitlines():
        line = rawLine.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        cleanKey = key.strip()
        cleanVal = val.strip().strip('"').strip("'")
        if cleanKey:
            parsed[cleanKey] = cleanVal
    return parsed


class Settings(BaseModel):
    """Typed runtime settings using camelCase attributes per AGENT_GUIDE §8."""

    appName: str = Field(default="EcoWatch API")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    databaseUrl: str = Field(
        default="postgresql+psycopg://ecowatch:ecowatch_dev@localhost:5433/ecowatch"
    )
    dbPoolSize: int = Field(default=10, ge=1, le=100)
    dbMaxOverflow: int = Field(default=10, ge=0, le=100)

    authSecret: str = Field(default="dev-only-insecure-secret-change-in-production")
    authTokenTtlSeconds: int = Field(default=3600 * 12, ge=60)

    storageRoot: Path = Field(default=Path("data/storage"))
    maxUploadBytes: int = Field(default=15 * 1024 * 1024, ge=1024)

    publicIntakeRateLimit: int = Field(default=30, ge=1)
    publicIntakeWindowSeconds: int = Field(default=60, ge=1)
    trackingLookupMaxAttempts: int = Field(default=5, ge=1)
    trackingLookupLockoutSeconds: int = Field(default=900, ge=10)

    workerEnabled: bool = Field(default=False)
    workerPollIntervalSeconds: float = Field(default=2.0, ge=0.2)
    workerBatchSize: int = Field(default=5, ge=1, le=50)
    workerMaxAttempts: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def validate_production_secret(self) -> Self:
        if (
            self.environment.lower() == "production"
            and self.authSecret == "dev-only-insecure-secret-change-in-production"
        ):
            raise ValueError("ECOWATCH_AUTH_SECRET must be set to a strong secret in production")
        return self

    @classmethod
    def from_env(cls, envPath: Path | None = None) -> Self:
        """Build Settings from process environment overlaid onto .env defaults."""
        dotenvMap = _load_dotenv_values(envPath or Path(".env"))
        envMap = {**dotenvMap, **os.environ}
        envKeys = {
            "appName": "ECOWATCH_APP_NAME",
            "environment": "ECOWATCH_ENV",
            "debug": "ECOWATCH_DEBUG",
            "databaseUrl": "DATABASE_URL",
            "dbPoolSize": "ECOWATCH_DB_POOL_SIZE",
            "dbMaxOverflow": "ECOWATCH_DB_MAX_OVERFLOW",
            "authSecret": "ECOWATCH_AUTH_SECRET",
            "authTokenTtlSeconds": "ECOWATCH_AUTH_TOKEN_TTL_SECONDS",
            "storageRoot": "ECOWATCH_STORAGE_ROOT",
            "maxUploadBytes": "ECOWATCH_MAX_UPLOAD_BYTES",
            "publicIntakeRateLimit": "ECOWATCH_PUBLIC_INTAKE_RATE_LIMIT",
            "publicIntakeWindowSeconds": "ECOWATCH_PUBLIC_INTAKE_WINDOW_SECONDS",
            "trackingLookupMaxAttempts": "ECOWATCH_TRACKING_LOOKUP_MAX_ATTEMPTS",
            "trackingLookupLockoutSeconds": "ECOWATCH_TRACKING_LOOKUP_LOCKOUT_SECONDS",
            "workerEnabled": "ECOWATCH_WORKER_ENABLED",
            "workerPollIntervalSeconds": "ECOWATCH_WORKER_POLL_INTERVAL_SECONDS",
            "workerBatchSize": "ECOWATCH_WORKER_BATCH_SIZE",
            "workerMaxAttempts": "ECOWATCH_WORKER_MAX_ATTEMPTS",
        }
        values = {
            attrName: envMap[envKey]
            for attrName, envKey in envKeys.items()
            if envKey in envMap and envMap[envKey] != ""
        }
        return cls(**values)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings.from_env()
