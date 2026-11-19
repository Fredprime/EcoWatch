"""Request size limits, concurrency bounds, timeouts, cache isolation, and metrics middleware."""

import asyncio
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ecowatch.core.config import Settings
from ecowatch.core.errors import ErrorCode
from ecowatch.core.metrics import metricsRegistry
from ecowatch.core.schemas import ErrorCategory, ErrorResponse

_PUBLIC_CACHEABLE_PATHS = frozenset(
    {
        "/api/v1/public/cases",
        "/api/v1/methods",
        "/api/v1/units",
    }
)
_MULTIPART_OVERHEAD_BYTES = 1024 * 1024


def _error_json(
    *,
    statusCode: int,
    code: ErrorCode,
    message: str,
    request: Request,
    category: ErrorCategory,
    retryAfterSeconds: int | None = None,
) -> JSONResponse:
    requestId = getattr(request.state, "requestId", None)
    body = ErrorResponse(
        code=code.value,
        message=message,
        requestId=requestId,
        category=category,
        retryAfterSeconds=retryAfterSeconds,
    )
    headers = {"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"}
    if retryAfterSeconds is not None:
        headers["Retry-After"] = str(retryAfterSeconds)
    return JSONResponse(
        status_code=statusCode,
        content=body.model_dump(by_alias=True),
        headers=headers,
    )


class RequestLimitsAndHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce body size limits, concurrency bounds, timeouts, cache isolation, and metrics."""

    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._semaphore = asyncio.Semaphore(settings.maxConcurrentRequests)

    async def dispatch(
        self, request: Request, callNext: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        contentLengthRaw = request.headers.get("content-length")
        if contentLengthRaw is not None:
            try:
                contentLength = int(contentLengthRaw)
            except ValueError:
                contentLength = -1
            contentType = (request.headers.get("content-type") or "").lower()
            maxAllowed = (
                self._settings.maxUploadBytes + _MULTIPART_OVERHEAD_BYTES
                if contentType.startswith("multipart/form-data")
                else self._settings.maxJsonBodyBytes
            )
            if contentLength < 0 or contentLength > maxAllowed:
                return _error_json(
                    statusCode=status.HTTP_413_CONTENT_TOO_LARGE,
                    code=ErrorCode.PAYLOAD_TOO_LARGE,
                    message=f"Request payload exceeds {maxAllowed} byte limit",
                    request=request,
                    category=ErrorCategory.PERMANENT,
                )

        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=0.05)
        except TimeoutError:
            metricsRegistry.record_response(status.HTTP_503_SERVICE_UNAVAILABLE, 50.0)
            return _error_json(
                statusCode=status.HTTP_503_SERVICE_UNAVAILABLE,
                code=ErrorCode.INTERNAL_ERROR,
                message="Server concurrency limit reached; please retry shortly",
                request=request,
                category=ErrorCategory.TRANSIENT,
                retryAfterSeconds=5,
            )

        metricsRegistry.inc_active()
        started = time.perf_counter()
        try:
            response = await asyncio.wait_for(
                callNext(request), timeout=self._settings.requestTimeoutSeconds
            )
        except TimeoutError:
            durationMs = round((time.perf_counter() - started) * 1000, 2)
            metricsRegistry.record_response(status.HTTP_504_GATEWAY_TIMEOUT, durationMs)
            return _error_json(
                statusCode=status.HTTP_504_GATEWAY_TIMEOUT,
                code=ErrorCode.INTERNAL_ERROR,
                message="Request timed out",
                request=request,
                category=ErrorCategory.TRANSIENT,
                retryAfterSeconds=5,
            )
        finally:
            metricsRegistry.dec_active()
            self._semaphore.release()

        durationMs = round((time.perf_counter() - started) * 1000, 2)
        metricsRegistry.record_response(response.status_code, durationMs)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        if "Cache-Control" not in response.headers:
            isPublicCacheable = (
                request.method in {"GET", "HEAD"}
                and request.url.path in _PUBLIC_CACHEABLE_PATHS
                and not request.headers.get("authorization")
                and response.status_code == status.HTTP_200_OK
            )
            if isPublicCacheable:
                response.headers["Cache-Control"] = "public, max-age=30"
            else:
                response.headers["Cache-Control"] = "no-store, private"
                response.headers.setdefault("Vary", "Authorization")
        return response
