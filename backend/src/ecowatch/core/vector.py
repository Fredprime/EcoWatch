"""Native pgvector column type with a JSON fallback for SQLite tests."""

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import UserDefinedType


class _PgVector(UserDefinedType):
    """SQLAlchemy DDL and binding for a fixed-dimension pgvector column."""

    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kw: Any) -> str:
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect: Any) -> Any:
        def process(value: list[float] | tuple[float, ...] | None) -> str | None:
            if value is None:
                return None
            return "[" + ",".join(f"{float(item):.6f}" for item in value) + "]"

        return process

    def result_processor(self, dialect: Any, coltype: Any) -> Any:
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, str):
                body = value.strip()
                if body.startswith("[") and body.endswith("]"):
                    body = body[1:-1]
                return [float(item) for item in body.split(",") if item.strip()]
            return [float(item) for item in value]

        return process


def VectorType(dimensions: int) -> Any:
    """Return pgvector on PostgreSQL and JSON text on SQLite."""
    return JSON().with_variant(_PgVector(dimensions), "postgresql")
