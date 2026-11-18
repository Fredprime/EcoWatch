"""Canonical enumerations for environmental intelligence."""

from enum import StrEnum


class EnvironmentalEntityType(StrEnum):
    """Kinds of environmental entity that observations can relate to."""

    SITE = "site"
    CATCHMENT = "catchment"
    SUB_CATCHMENT = "sub_catchment"
    WATERBODY = "waterbody"
    HABITAT = "habitat"
    MONITORED_ASSET = "monitored_asset"


class EnvironmentalRelationshipType(StrEnum):
    """Supported evidence-backed relationships between environmental endpoints."""

    UPSTREAM_DOWNSTREAM = "upstream_downstream"
    SOURCE_PATHWAY_RECEPTOR = "source_pathway_receptor"
    HABITAT_CONNECTIVITY = "habitat_connectivity"
    TEMPORAL_ASSOCIATION = "temporal_association"
    SPATIAL_ADJACENCY = "spatial_adjacency"


class UncertaintyLevel(StrEnum):
    """Declared confidence in an environmental relationship."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ReviewState(StrEnum):
    """Human review state for a proposed environmental relationship."""

    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    CONTESTED = "contested"


class AnalysisType(StrEnum):
    """Supported reproducible analysis families."""

    LAND_COVER_CHANGE = "land_cover_change"
    WATER_QUALITY_COMPARISON = "water_quality_comparison"
    HISTORICAL_COMPARISON = "historical_comparison"
    CUSTOM = "custom"


class AnalysisStatus(StrEnum):
    """Lifecycle status of an analysis run."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisOutputType(StrEnum):
    """Kinds of derived analysis output."""

    MAP = "map"
    METRIC = "metric"
    TABLE = "table"
    REPORT = "report"
    RASTER = "raster"


class InterpretationState(StrEnum):
    """Human interpretation state of a derived analysis output."""

    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    DISPUTED = "disputed"
