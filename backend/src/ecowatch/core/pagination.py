"""Opaque cursor encoding, decoding, and shared keyset pagination helper."""

import base64
import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import status
from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode


def encode_cursor(timestamp: datetime, recordId: uuid.UUID) -> str:
    """Encode a stable (timestamp, UUID) cursor for keyset pagination."""
    payload = {"t": timestamp.isoformat(), "id": str(recordId)}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decode and validate an opaque pagination cursor."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        payload = json.loads(raw)
        timestamp = datetime.fromisoformat(payload["t"])
        recordId = uuid.UUID(payload["id"])
        return timestamp, recordId
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid pagination cursor",
            statusCode=status.HTTP_400_BAD_REQUEST,
            field="cursor",
        ) from exc


def paginate_descending(
    session: Session,
    stmt: Select[Any],
    *,
    timeCol: Any,
    idCol: Any,
    cursor: str | None,
    limit: int,
) -> tuple[list[Any], str | None, bool]:
    """Apply descending (timeCol, idCol) keyset pagination to any SQLAlchemy select."""
    boundedLimit = max(1, min(limit, 100))
    if cursor is not None:
        cursorTime, cursorId = decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                timeCol < cursorTime,
                and_(timeCol == cursorTime, idCol < cursorId),
            )
        )
    ordered = stmt.order_by(timeCol.desc(), idCol.desc()).limit(boundedLimit + 1)
    rows = list(session.execute(ordered).scalars().all())
    hasMore = len(rows) > boundedLimit
    pageItems = rows[:boundedLimit]
    nextCursor = None
    if hasMore and pageItems:
        lastItem = pageItems[-1]
        lastTime = getattr(lastItem, timeCol.key, None) or getattr(
            lastItem, _snake_to_camel(timeCol.key)
        )
        nextCursor = encode_cursor(lastTime, lastItem.id)
    return pageItems, nextCursor, hasMore


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


__all__ = [
    "decode_cursor",
    "encode_cursor",
    "paginate_descending",
    "select",
]
