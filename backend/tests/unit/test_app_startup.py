"""Application startup regression checks for the optional background worker."""

import asyncio
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from ecowatch.core.config import Settings
from ecowatch.main import create_app


def test_worker_enabled_startup_passes_stop_event_as_keyword(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_worker_loop(_sessionFactory: object, _storage: object, **kwargs: object) -> object:
        captured.update(kwargs)

        async def wait_until_cancelled() -> None:
            await asyncio.Event().wait()

        return wait_until_cancelled()

    settings = Settings(
        environment="test",
        authSecret="test-secret-key-for-ecowatch-phase1",
        storageRoot=tmp_path / "storage",
        workerEnabled=True,
    )
    with (
        patch("ecowatch.main.worker_loop", fake_worker_loop),
        patch("ecowatch.main.get_session_factory", return_value=object()),
        TestClient(create_app(settings)),
    ):
        pass

    assert isinstance(captured.get("stopEvent"), asyncio.Event)
    assert captured["pollIntervalSeconds"] == settings.workerPollIntervalSeconds
    assert captured["batchSize"] == settings.workerBatchSize
    assert captured["maxAttempts"] == settings.workerMaxAttempts
