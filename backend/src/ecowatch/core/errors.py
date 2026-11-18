"""Finite domain error catalogue and FastAPI exception handlers."""

from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ecowatch.core.schemas import ErrorDetail, ErrorResponse


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
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.statusCode = statusCode
        self.field = field
        self.details = details or []


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
        )
        return JSONResponse(status_code=exc.statusCode, content=body.model_dump(by_alias=True))

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
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(by_alias=True),
        )
