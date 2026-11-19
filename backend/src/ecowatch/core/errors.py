"""Finite domain error catalogue and FastAPI exception handlers."""

from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ecowatch.core.schemas import ErrorCategory, ErrorDetail, ErrorResponse

DEFAULT_RETRY_AFTER_SECONDS = 30


class ErrorCode(StrEnum):
    """Finite API error codes across Phase 1."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    IDEMPOTENCY_KEY_CONFLICT = "IDEMPOTENCY_KEY_CONFLICT"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    SELF_REVIEW_FORBIDDEN = "SELF_REVIEW_FORBIDDEN"
    TWO_KEY_APPROVAL_REQUIRED = "TWO_KEY_APPROVAL_REQUIRED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TRACKING_CODE_LOCKED = "TRACKING_CODE_LOCKED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    EVIDENCE_NOT_READY = "EVIDENCE_NOT_READY"
    EVIDENCE_QUARANTINED = "EVIDENCE_QUARANTINED"
    PREDICTION_BLOCKED = "PREDICTION_BLOCKED"
    RECOVERY_NOT_VERIFIABLE = "RECOVERY_NOT_VERIFIABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# A retry can plausibly succeed for these codes even when the HTTP status alone
# would suggest a permanent failure (EVIDENCE_NOT_READY is a 409 but scan
# completion resolves it). Everything else is permanent unless the status is
# 429 or 5xx, which is classified by classify_error() below.
_TRANSIENT_ERROR_CODES = frozenset(
    {
        ErrorCode.RATE_LIMIT_EXCEEDED,
        ErrorCode.TRACKING_CODE_LOCKED,
        ErrorCode.EVIDENCE_NOT_READY,
    }
)


def classify_error(code: ErrorCode, statusCode: int) -> ErrorCategory:
    """Classify a domain error as permanent (do not retry) or transient (retry)."""
    if statusCode >= 500 or statusCode == status.HTTP_429_TOO_MANY_REQUESTS:
        return ErrorCategory.TRANSIENT
    if code in _TRANSIENT_ERROR_CODES:
        return ErrorCategory.TRANSIENT
    return ErrorCategory.PERMANENT


class DomainError(Exception):
    """Application exception mapped cleanly to a finite HTTP error response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        statusCode: int = status.HTTP_400_BAD_REQUEST,
        field: str | None = None,
        details: list[ErrorDetail] | None = None,
        category: ErrorCategory | None = None,
        retryAfterSeconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.statusCode = statusCode
        self.field = field
        self.details = details or []
        self.category = category or classify_error(code, statusCode)
        self.retryAfterSeconds = retryAfterSeconds


def register_exception_handlers(app: FastAPI) -> None:
    """Attach domain, validation, and fallback exception handlers."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        requestId = getattr(request.state, "requestId", None)
        body = ErrorResponse(
            code=exc.code.value,
            message=exc.message,
            field=exc.field,
            details=exc.details,
            requestId=requestId,
            category=exc.category,
            retryAfterSeconds=exc.retryAfterSeconds,
        )
        headers = {}
        if exc.retryAfterSeconds is not None:
            headers["Retry-After"] = str(exc.retryAfterSeconds)
        return JSONResponse(
            status_code=exc.statusCode,
            content=body.model_dump(by_alias=True),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        requestId = getattr(request.state, "requestId", None)
        details = [
            ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR.value,
                message=err.get("msg", "Invalid input"),
                field=".".join(str(part) for part in err.get("loc", []) if part != "body") or None,
            )
            for err in exc.errors()
        ]
        body = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR.value,
            message="Request validation failed",
            details=details,
            requestId=requestId,
            category=ErrorCategory.PERMANENT,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=body.model_dump(by_alias=True),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        requestId = getattr(request.state, "requestId", None)
        body = ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="An unexpected error occurred",
            requestId=requestId,
            category=ErrorCategory.TRANSIENT,
            retryAfterSeconds=DEFAULT_RETRY_AFTER_SECONDS,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(by_alias=True),
            headers={"Retry-After": str(DEFAULT_RETRY_AFTER_SECONDS)},
        )
