"""Shared Pydantic boundary schemas enforcing camelCase payloads."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base Pydantic schema mapping camelCase JSON and camelCase Python attributes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class CursorPage[T](CamelModel):
    """Standard cursor-paginated list response."""

    items: list[T]
    nextCursor: str | None = None
    hasMore: bool = False


class ErrorDetail(CamelModel):
    """Field-level validation or domain error item."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(CamelModel):
    """Stable API error envelope without internal stack traces."""

    code: str
    message: str
    field: str | None = None
    details: list[ErrorDetail] = Field(default_factory=list)
    requestId: str | None = None
