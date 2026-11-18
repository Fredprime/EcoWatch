"""Allowlist-based structured logging preventing accidental PII or secret exposure."""

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

ALLOWED_LOG_FIELDS = frozenset(
    {
        "timestamp",
        "level",
        "event",
        "requestId",
        "method",
        "path",
        "statusCode",
        "durationMs",
        "actorRole",
        "jobId",
        "jobType",
        "errorCode",
    }
)


class AllowlistJsonFormatter(logging.Formatter):
    """Formats log records as JSON containing only allowlisted non-PII fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        extraFields = getattr(record, "structured", None)
        if isinstance(extraFields, dict):
            for key, value in extraFields.items():
                if key in ALLOWED_LOG_FIELDS:
                    payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    """Configure the root ecowatch logger with the PII-safe allowlist formatter."""
    logger = logging.getLogger("ecowatch")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(AllowlistJsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID header and emits allowlisted HTTP access logs."""

    def __init__(self, app, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self._logger = logger or configure_logging()

    async def dispatch(
        self, request: Request, callNext: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        requestId = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.requestId = requestId
        started = time.perf_counter()
        response = await callNext(request)
        durationMs = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = requestId
        self._logger.info(
            "http_request",
            extra={
                "structured": {
                    "requestId": requestId,
                    "method": request.method,
                    "path": request.url.path,
                    "statusCode": response.status_code,
                    "durationMs": durationMs,
                }
            },
        )
        return response
