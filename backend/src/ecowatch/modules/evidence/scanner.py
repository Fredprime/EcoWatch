"""Pure content-inspection, EXIF extraction, and EXIF-stripped preview generation."""

import csv
import io
import json
from pathlib import PurePosixPath
from typing import Any

from PIL import ExifTags, Image, ImageOps

from ecowatch.modules.evidence.models import MetadataExtractionStatus, ScanStatus

ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
        "text/csv",
        "application/json",
    }
)
IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

_DANGEROUS_PREFIXES: tuple[bytes, ...] = (
    b"\x7fELF",
    b"MZ",
    b"#!",
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"PK\x03\x04",
)


def normalize_declared_mime(mimeType: str | None) -> str:
    """Normalize a declared MIME type string without parameters."""
    if not mimeType:
        return "application/octet-stream"
    base = mimeType.split(";", 1)[0].strip().lower()
    if base == "image/jpg":
        return "image/jpeg"
    return base or "application/octet-stream"


def sanitize_filename(filename: str | None) -> str:
    """Extract a safe metadata-only basename; never used as a storage path."""
    if not filename:
        return "evidence.bin"
    base = PurePosixPath(filename.replace("\\", "/")).name
    cleaned = "".join(ch for ch in base if 32 <= ord(ch) < 127 and ch not in {"/", "\\"})
    cleaned = cleaned.strip().lstrip(".")
    return cleaned[:255] if cleaned else "evidence.bin"


def detect_mime_from_bytes(
    data: bytes, declaredMimeType: str | None = None
) -> str | None:
    """Detect allowed MIME types strictly from file content/magic bytes."""
    if not data or any(data.startswith(prefix) for prefix in _DANGEROUS_PREFIXES):
        return None

    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF-"):
        return "application/pdf"

    if b"\x00" in data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None

    stripped = text.lstrip()
    if not stripped:
        return None

    declared = normalize_declared_mime(declaredMimeType)
    if declared == "application/json" or (
        declared == "application/octet-stream" and stripped[0] in {"{", "["}
    ):
        try:
            json.loads(text)
            return "application/json"
        except json.JSONDecodeError:
            return None

    if declared == "text/csv":
        if any(ord(ch) < 32 and ch not in {"\r", "\n", "\t"} for ch in text):
            return None
        try:
            list(csv.reader(io.StringIO(text)))
            return "text/csv"
        except csv.Error:
            return None

    return None


def is_mime_compatible(detectedMime: str | None, declaredMime: str | None) -> bool:
    """Verify detected MIME is allowlisted and matches any explicit non-generic declaration."""
    if detectedMime is None or detectedMime not in ALLOWED_MIME_TYPES:
        return False
    normalized = normalize_declared_mime(declaredMime)
    if normalized == "application/octet-stream":
        return True
    return normalized == detectedMime


def _json_safe_exif_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:200]
    if isinstance(value, (list, tuple)):
        return [_json_safe_exif_value(item) for item in value[:32]]
    if isinstance(value, dict):
        return {str(k): _json_safe_exif_value(v) for k, v in value.items()}
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)[:200]


def extract_image_metadata(
    data: bytes,
) -> tuple[MetadataExtractionStatus, dict[str, Any] | None]:
    """Safely extract basic image dimensions and JSON-safe EXIF tags via Pillow."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            metadata: dict[str, Any] = {
                "format": img.format,
                "mode": img.mode,
                "width": width,
                "height": height,
            }
            rawExif = img.getexif()
            if rawExif:
                exifDict = {
                    str(ExifTags.TAGS.get(tagId, tagId)): _json_safe_exif_value(val)
                    for tagId, val in rawExif.items()
                }
                if exifDict:
                    metadata["exif"] = exifDict
            return MetadataExtractionStatus.EXTRACTED, metadata
    except Exception:
        return MetadataExtractionStatus.FAILED, None


def create_exif_stripped_preview(
    data: bytes,
    mimeType: str,
    *,
    maxDimension: int = 1600,
) -> tuple[bytes, str]:
    """Generate an EXIF-stripped image preview preserving visual orientation."""
    with Image.open(io.BytesIO(data)) as source:
        transposed = ImageOps.exif_transpose(source)
        transposed.thumbnail((maxDimension, maxDimension))

        output = io.BytesIO()
        if mimeType == "image/png":
            if transposed.mode not in {"RGB", "RGBA", "L", "LA"}:
                transposed = transposed.convert("RGBA")
            transposed.save(output, format="PNG")
            return output.getvalue(), "image/png"

        if mimeType == "image/webp":
            if transposed.mode not in {"RGB", "RGBA"}:
                transposed = transposed.convert("RGBA")
            transposed.save(output, format="WEBP", quality=85)
            return output.getvalue(), "image/webp"

        if transposed.mode != "RGB":
            transposed = transposed.convert("RGB")
        transposed.save(output, format="JPEG", quality=85)
        return output.getvalue(), "image/jpeg"


def scan_evidence_bytes(
    data: bytes, expectedMimeType: str
) -> tuple[ScanStatus, str | None]:
    """Perform content integrity and safety verification on stored evidence bytes."""
    detected = detect_mime_from_bytes(data, expectedMimeType)
    if detected is None or detected != expectedMimeType:
        return ScanStatus.REJECTED, "Content signature mismatch"

    if detected in IMAGE_MIME_TYPES:
        try:
            with Image.open(io.BytesIO(data)) as img:
                img.verify()
            with Image.open(io.BytesIO(data)) as img:
                img.load()
        except Exception:
            return ScanStatus.QUARANTINED, "Corrupt or malformed image payload"

    return ScanStatus.CLEAN, None
