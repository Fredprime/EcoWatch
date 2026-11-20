"""FastAPI application factory and lifespan management for EcoWatch Phase 1."""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ecowatch.api.router import apiRouter
from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import get_session_factory
from ecowatch.core.errors import register_exception_handlers
from ecowatch.core.logging import RequestIdMiddleware, configure_logging
from ecowatch.core.middleware import RequestLimitsAndHeadersMiddleware
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.modules.jobs.worker import worker_loop


def create_app(settingsOverride: Settings | None = None) -> FastAPI:
    """Construct the EcoWatch FastAPI modular monolith application."""
    settings = settingsOverride or get_settings()
    logger = configure_logging()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        settings.storageRoot.mkdir(parents=True, exist_ok=True)
        stopEvent = asyncio.Event()
        workerTask: asyncio.Task[None] | None = None
        if settings.workerEnabled:
            storage = LocalFilesystemStorage(settings.storageRoot)
            workerTask = asyncio.create_task(
                worker_loop(
                    get_session_factory(),
                    storage,
                    pollIntervalSeconds=settings.workerPollIntervalSeconds,
                    batchSize=settings.workerBatchSize,
                    maxAttempts=settings.workerMaxAttempts,
                    stopEvent=stopEvent,
                )
            )
        try:
            yield
        finally:
            stopEvent.set()
            if workerTask is not None:
                workerTask.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await workerTask

    application = FastAPI(
        title=settings.appName,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(RequestLimitsAndHeadersMiddleware, settings=settings)
    application.add_middleware(GZipMiddleware, minimum_size=settings.gzipMinimumSize)
    application.add_middleware(RequestIdMiddleware, logger=logger)
    corsOrigins = [origin.strip() for origin in settings.corsOrigins.split(",") if origin.strip()]
    if corsOrigins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=corsOrigins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_exception_handlers(application)
    application.include_router(apiRouter)
    return application


app = create_app()
