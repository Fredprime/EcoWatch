"""Native PostGIS Geography column type and lightweight WKT validation/helpers."""

import re
from typing import Any

from sqlalchemy import Text, func
from sqlalchemy.types import UserDefinedType

_WKT_HEADER_RE = re.compile(
    r"^\s*(?:SRID=\d+;)?\s*(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON)"
    r"\s*\((.+)\)\s*$",
    re.IGNORECASE | re.DOTALL,
)
_COORD_PAIR_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")
_POINT_RE = re.compile(
    r"^\s*(?:SRID=4326;)?\s*POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)\s*$",
    re.IGNORECASE,
)


class _PostGISGeography(UserDefinedType):
    """Native SQLAlchemy DDL emitter for PostgreSQL PostGIS GEOGRAPHY columns."""

    cache_ok = True

    def __init__(self, geometryType: str = "POINT", srid: int = 4326) -> None:
        self.geometryType = geometryType
        self.srid = srid

    def get_col_spec(self, **_kw: Any) -> str:
        return f"GEOGRAPHY({self.geometryType}, {self.srid})"


def GeographyType(geometryType: str = "POINT", srid: int = 4326) -> Any:
    """Return PostGIS GEOGRAPHY on PostgreSQL and TEXT (WKT) on SQLite."""
    return Text().with_variant(
        _PostGISGeography(geometryType=geometryType, srid=srid), "postgresql"
    )


def validate_wkt_geometry(wktText: str) -> str:
    """Validate basic WKT geometry syntax and WGS84 coordinate bounds without Shapely."""
    stripped = wktText.strip()
    match = _WKT_HEADER_RE.match(stripped)
    if not match:
        raise ValueError("Invalid WKT geometry format")
    coordBody = match.group(2)
    pairs = _COORD_PAIR_RE.findall(coordBody)
    if not pairs:
        raise ValueError("WKT geometry contains no coordinate pairs")
    for lonStr, latStr in pairs:
        lonVal = float(lonStr)
        latVal = float(latStr)
        if not (-180.0 <= lonVal <= 180.0 and -90.0 <= latVal <= 90.0):
            raise ValueError("Geometry coordinates out of WGS84 bounds")
    return stripped


def format_point_wkt(longitude: float, latitude: float) -> str:
    """Format a WGS84 point as canonical WKT."""
    return f"POINT({longitude} {latitude})"


def parse_point_wkt(rawValue: Any) -> tuple[float, float] | None:
    """Parse a stored WKT POINT string into (longitude, latitude)."""
    if rawValue is None:
        return None
    if not isinstance(rawValue, str):
        rawValue = str(rawValue)
    match = _POINT_RE.match(rawValue)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def coarsen_point_wkt(longitude: float, latitude: float, *, decimals: int = 2) -> str:
    """Generalise a coordinate to ~1.1 km precision for public/sensitive views."""
    return format_point_wkt(round(longitude, decimals), round(latitude, decimals))


def geography_to_text_expr(column: Any, dialectName: str) -> Any:
    """Select WKT text on PostgreSQL (ST_AsText) or directly on SQLite."""
    if dialectName == "postgresql":
        return func.ST_AsText(column)
    return column
