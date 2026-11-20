"""Local structural validation rules for evidence assets (no external services)."""

from __future__ import annotations

from typing import Any

MAX_IMAGE_WIDTH = 10_000
MAX_IMAGE_HEIGHT = 10_000
MAX_IMAGE_PIXELS = 40_000_000


def image_dimensions_within_bounds(metadata: dict[str, Any] | None) -> tuple[bool, str | None]:
    """Reject implausibly large decoded images using already-parsed dimensions.

    Returns (True, None) when dimensions are absent so that the existing byte-level
    integrity scan stays authoritative for anything this check cannot measure.
    """
    if not metadata:
        return True, None
    width = metadata.get("width")
    height = metadata.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return True, None
    if (
        width <= 0
        or height <= 0
        or width > MAX_IMAGE_WIDTH
        or height > MAX_IMAGE_HEIGHT
        or width * height > MAX_IMAGE_PIXELS
    ):
        return False, (
            f"Decoded image dimensions {width}x{height} exceed local structural "
            f"bounds ({MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}, {MAX_IMAGE_PIXELS} pixels)"
        )
    return True, None
