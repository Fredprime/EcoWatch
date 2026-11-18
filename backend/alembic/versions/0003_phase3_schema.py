"""Phase 3 schema: catalogue, intelligence, prioritisation, interventions, verification.

Rollback note: downgrade drops Phase 3 tables in reverse dependency order and leaves
Phase 1 tables, shared extensions, and existing data untouched.

Revision ID: 0003_phase3_schema
Revises: 0002_phase2_correlation
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from ecowatch.core.spatial import GeographyType

revision: str = "0003_phase3_schema"
down_revision: str | Sequence[str] | None = "0002_phase2_correlation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    isPostgres = bind.dialect.name == "postgresql"

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=200), nullable=False),
        sa.Column("licence", sa.String(length=200), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=False),
        sa.Column("permitted_use", sa.Text(), nullable=False),
        sa.Column("crs", sa.String(length=50), nullable=False),
        sa.Column("coverage_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("coverage_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("coverage_geometry", GeographyType("GEOMETRY", 4326), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organisation_id", "name", name="uq_datasets_organisation_name"
        ),
    )
    op.create_index("ix_datasets_organisation_id", "datasets", ["organisation_id"])

    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("datasets.id"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(length=100), nullable=False),
        sa.Column("source_acquisition_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution", sa.String(length=100), nullable=False),
        sa.Column("crs", sa.String(length=50), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("quality_notes", sa.Text(), nullable=True),
        sa.Column("licence_snapshot", sa.String(length=200), nullable=False),
        sa.Column("attribution_snapshot", sa.Text(), nullable=False),
        sa.Column("permitted_use_snapshot", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "version_label", name="uq_dataset_versions_label"),
    )
    op.create_index(
        "ix_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"]
    )

    op.create_table(
        "environmental_entities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("geometry", GeographyType("GEOMETRY", 4326), nullable=True),
        sa.Column("crs", sa.String(length=50), nullable=False),
        sa.Column(
            "parent_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("environmental_entities.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_environmental_entities_organisation_id",
        "environmental_entities",
        ["organisation_id"],
    )

    op.create_table(
        "environmental_relationships",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column(
            "from_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("environmental_entities.id"),
            nullable=True,
        ),
        sa.Column(
            "from_observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=True,
        ),
        sa.Column(
            "to_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("environmental_entities.id"),
            nullable=True,
        ),
        sa.Column(
            "to_observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=True,
        ),
        sa.Column("spatial_scope", sa.Text(), nullable=True),
        sa.Column("temporal_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("temporal_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("supporting_evidence_asset_ids", sa.JSON(), nullable=False),
        sa.Column("method_name", sa.String(length=200), nullable=False),
        sa.Column("method_version", sa.String(length=100), nullable=False),
        sa.Column("uncertainty", sa.String(length=20), nullable=False),
        sa.Column("uncertainty_note", sa.Text(), nullable=False),
        sa.Column("alternative_explanations", sa.Text(), nullable=False),
        sa.Column("review_state", sa.String(length=20), nullable=False),
        sa.Column(
            "reviewed_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_environmental_relationships_organisation_id",
        "environmental_relationships",
        ["organisation_id"],
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column("method_name", sa.String(length=200), nullable=False),
        sa.Column("method_version", sa.String(length=100), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("input_dataset_version_ids", sa.JSON(), nullable=False),
        sa.Column("crs", sa.String(length=50), nullable=False),
        sa.Column("quality_mask_notes", sa.Text(), nullable=True),
        sa.Column("seasonal_context", sa.Text(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "requested_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_runs_organisation_id", "analysis_runs", ["organisation_id"])
    op.create_index("ix_analysis_runs_case_id", "analysis_runs", ["case_id"])
    op.create_index("ix_analysis_runs_status", "analysis_runs", ["status"])

    op.create_table(
        "analysis_outputs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_run_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("analysis_runs.id"),
            nullable=False,
        ),
        sa.Column("output_type", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("is_derived", sa.Boolean(), nullable=False),
        sa.Column("derived_from_observation_ids", sa.JSON(), nullable=False),
        sa.Column("interpretation_state", sa.String(length=30), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_analysis_outputs_analysis_run_id",
        "analysis_outputs",
        ["analysis_run_id"],
    )

    op.create_table(
        "prioritisation_assessments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False
        ),
        sa.Column("assessment_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method_name", sa.String(length=200), nullable=False),
        sa.Column("method_version", sa.String(length=100), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("missing_inputs", sa.JSON(), nullable=False),
        sa.Column("composite_rank", sa.Numeric(12, 4), nullable=True),
        sa.Column("ranking_method_ref", sa.Text(), nullable=True),
        sa.Column("rank_is_not_severity", sa.Boolean(), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column(
            "decided_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reviewer_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_prioritisation_assessments_organisation_id",
        "prioritisation_assessments",
        ["organisation_id"],
    )
    op.create_index(
        "ix_prioritisation_assessments_case_id",
        "prioritisation_assessments",
        ["case_id"],
    )

    op.create_table(
        "interventions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False
        ),
        sa.Column("additional_case_ids", sa.JSON(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column(
            "responsible_organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "authorised_lead_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("approval_reference", sa.Text(), nullable=True),
        sa.Column("location", GeographyType("GEOMETRY", 4326), nullable=True),
        sa.Column("affected_area_notes", sa.Text(), nullable=True),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("resources_notes", sa.Text(), nullable=True),
        sa.Column("intended_outcome", sa.Text(), nullable=True),
        sa.Column("indicator_definition_ids", sa.JSON(), nullable=False),
        sa.Column("baseline_summary", sa.Text(), nullable=True),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("follow_up_schedule", sa.Text(), nullable=True),
        sa.Column("verification_assessment_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_interventions_organisation_id", "interventions", ["organisation_id"])
    op.create_index("ix_interventions_case_id", "interventions", ["case_id"])
    op.create_index("ix_interventions_status", "interventions", ["status"])

    op.create_table(
        "intervention_milestones",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "intervention_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("interventions.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("evidence_asset_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_intervention_milestones_intervention_id",
        "intervention_milestones",
        ["intervention_id"],
    )

    op.create_table(
        "indicator_definitions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "unit_id", sa.Uuid(as_uuid=True), sa.ForeignKey("units.id"), nullable=False
        ),
        sa.Column("method_name", sa.String(length=200), nullable=False),
        sa.Column("method_version", sa.String(length=100), nullable=False),
        sa.Column("criteria_version", sa.String(length=100), nullable=True),
        sa.Column(
            "approved_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organisation_id", "code", name="uq_indicator_definitions_code"
        ),
    )
    op.create_index(
        "ix_indicator_definitions_organisation_id",
        "indicator_definitions",
        ["organisation_id"],
    )

    op.create_table(
        "indicator_measurements",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "indicator_definition_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("indicator_definitions.id"),
            nullable=False,
        ),
        sa.Column(
            "intervention_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("interventions.id"),
            nullable=True,
        ),
        sa.Column(
            "case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True
        ),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=True,
        ),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(20, 6), nullable=True),
        sa.Column("qualifier", sa.String(length=20), nullable=False),
        sa.Column("detection_limit", sa.Numeric(20, 6), nullable=True),
        sa.Column(
            "unit_id", sa.Uuid(as_uuid=True), sa.ForeignKey("units.id"), nullable=False
        ),
        sa.Column("method_name", sa.String(length=200), nullable=False),
        sa.Column("method_version", sa.String(length=100), nullable=False),
        sa.Column("quality_controls", sa.Text(), nullable=True),
        sa.Column("uncertainty_note", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_indicator_measurements_organisation_id",
        "indicator_measurements",
        ["organisation_id"],
    )
    op.create_index(
        "ix_indicator_measurements_indicator_definition_id",
        "indicator_measurements",
        ["indicator_definition_id"],
    )
    op.create_index(
        "ix_indicator_measurements_intervention_id",
        "indicator_measurements",
        ["intervention_id"],
    )

    op.create_table(
        "verification_assessments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "intervention_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("interventions.id"),
            nullable=False,
        ),
        sa.Column("baseline_measurement_ids", sa.JSON(), nullable=False),
        sa.Column("follow_up_measurement_ids", sa.JSON(), nullable=False),
        sa.Column("comparison_method", sa.Text(), nullable=False),
        sa.Column("confounders", sa.Text(), nullable=True),
        sa.Column("seasonality_notes", sa.Text(), nullable=True),
        sa.Column("uncertainty_note", sa.Text(), nullable=True),
        sa.Column("conclusion", sa.String(length=30), nullable=False),
        sa.Column("criteria_version", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "reviewed_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_verification_assessments_organisation_id",
        "verification_assessments",
        ["organisation_id"],
    )
    op.create_index(
        "ix_verification_assessments_intervention_id",
        "verification_assessments",
        ["intervention_id"],
    )

    op.create_table(
        "publications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "verification_assessment_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("verification_assessments.id"),
            nullable=True,
        ),
        sa.Column(
            "case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True
        ),
        sa.Column("published_text", sa.Text(), nullable=False),
        sa.Column(
            "approved_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("approved_role", sa.String(length=50), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_publications_organisation_id", "publications", ["organisation_id"])

    if isPostgres:
        op.execute(
            "CREATE INDEX ix_datasets_coverage_geometry_gist "
            "ON datasets USING GIST (coverage_geometry)"
        )
        op.execute(
            "CREATE INDEX ix_environmental_entities_geometry_gist "
            "ON environmental_entities USING GIST (geometry)"
        )
        op.execute(
            "CREATE INDEX ix_interventions_location_gist "
            "ON interventions USING GIST (location)"
        )


def downgrade() -> None:
    op.drop_table("publications")
    op.drop_table("verification_assessments")
    op.drop_table("indicator_measurements")
    op.drop_table("indicator_definitions")
    op.drop_table("intervention_milestones")
    op.drop_table("interventions")
    op.drop_table("prioritisation_assessments")
    op.drop_table("analysis_outputs")
    op.drop_table("analysis_runs")
    op.drop_table("environmental_relationships")
    op.drop_table("environmental_entities")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
