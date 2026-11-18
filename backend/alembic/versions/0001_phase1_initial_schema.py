"""Phase 1 initial schema: identity, observations, evidence, cases, audit, jobs, notifications.

Rollback note: downgrade drops all Phase 1 tables in reverse dependency order without
dropping the PostGIS extension itself so shared database extensions remain intact.

Revision ID: 0001_phase1_initial_schema
Revises:
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from ecowatch.core.spatial import GeographyType

revision: str = "0001_phase1_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    isPostgres = bind.dialect.name == "postgresql"
    if isPostgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "rate_limit_buckets",
        sa.Column("bucket_key", sa.String(length=255), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("system_role", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "organisations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("org_type", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "user_id", "organisation_id", "role", name="uq_memberships_user_org_role"
        ),
    )
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_memberships_organisation_id", "memberships", ["organisation_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", sa.String(length=64), nullable=False),
        sa.Column("organisation_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_organisation_id", "audit_events", ["organisation_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_target", "audit_events", ["target_type", "target_id"])

    op.create_table(
        "methods",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("protocol_text", sa.Text(), nullable=True),
        sa.Column("instrument_class", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("ucum_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.Uuid(as_uuid=True), nullable=False, unique=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("tracking_code_hash", sa.String(length=64), nullable=True),
        sa.Column("observation_type", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_firsthand", sa.Boolean(), nullable=True),
        sa.Column("structured_data", sa.JSON(), nullable=True),
        sa.Column("method_id", sa.Uuid(as_uuid=True), sa.ForeignKey("methods.id"), nullable=True),
        sa.Column("unit_id", sa.Uuid(as_uuid=True), sa.ForeignKey("units.id"), nullable=True),
        sa.Column("instrument", sa.String(length=120), nullable=True),
        sa.Column("event_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_precision", sa.String(length=32), nullable=False),
        sa.Column("original_time_wording", sa.String(length=200), nullable=True),
        sa.Column("location", GeographyType("POINT", 4326), nullable=True),
        sa.Column("public_location", GeographyType("POINT", 4326), nullable=True),
        sa.Column("location_precision", sa.String(length=32), nullable=False),
        sa.Column("original_location_wording", sa.String(length=200), nullable=True),
        sa.Column("quality_flags", sa.JSON(), nullable=False),
        sa.Column("access_class", sa.String(length=32), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "submitted_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("current_version >= 1", name="ck_observations_current_version_pos"),
        sa.CheckConstraint(
            "observed_end_at IS NULL OR observed_at IS NULL OR observed_end_at >= observed_at",
            name="ck_observations_time_range_valid",
        ),
    )
    op.create_index("ix_observations_organisation_id", "observations", ["organisation_id"])
    op.create_index("ix_observations_tracking_code_hash", "observations", ["tracking_code_hash"])
    op.create_index("ix_observations_observation_type", "observations", ["observation_type"])
    op.create_index("ix_observations_source_type", "observations", ["source_type"])
    op.create_index("ix_observations_method_id", "observations", ["method_id"])
    op.create_index("ix_observations_unit_id", "observations", ["unit_id"])
    op.create_index("ix_observations_observed_at", "observations", ["observed_at"])
    op.create_index("ix_observations_received_at", "observations", ["received_at"])
    op.create_index(
        "ix_observations_submitted_by_user_id", "observations", ["submitted_by_user_id"]
    )
    if isPostgres:
        op.execute(
            "CREATE INDEX ix_observations_location_gist ON observations USING GIST (location)"
        )
        op.execute(
            "CREATE INDEX ix_observations_public_location_gist "
            "ON observations USING GIST (public_location)"
        )

    op.create_table(
        "observation_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "edited_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "observation_id", "version_number", name="uq_observation_versions_obs_version"
        ),
    )
    op.create_index(
        "ix_observation_versions_observation_id", "observation_versions", ["observation_id"]
    )

    op.create_table(
        "observation_sources",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("reporter_name", sa.String(length=200), nullable=True),
        sa.Column("contact_channel", sa.String(length=64), nullable=True),
        sa.Column("contact_value", sa.String(length=255), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("privacy_notice_version", sa.String(length=64), nullable=False),
        sa.Column("safety_ack", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("client_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evidence_assets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("declared_mime_type", sa.String(length=120), nullable=False),
        sa.Column("detected_mime_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
        sa.Column("scan_status", sa.String(length=32), nullable=False),
        sa.Column("metadata_extraction_status", sa.String(length=32), nullable=False),
        sa.Column("extracted_metadata", sa.JSON(), nullable=True),
        sa.Column("access_class", sa.String(length=32), nullable=False),
        sa.Column(
            "uploaded_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_evidence_assets_size_pos"),
    )
    op.create_index("ix_evidence_assets_observation_id", "evidence_assets", ["observation_id"])
    op.create_index("ix_evidence_assets_organisation_id", "evidence_assets", ["organisation_id"])
    op.create_index("ix_evidence_assets_sha256_checksum", "evidence_assets", ["sha256_checksum"])
    op.create_index("ix_evidence_assets_scan_status", "evidence_assets", ["scan_status"])

    op.create_table(
        "asset_derivatives",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "parent_asset_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evidence_assets.id"),
            nullable=False,
        ),
        sa.Column("derivative_type", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
        sa.Column("exif_stripped", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("access_class", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_asset_derivatives_size_pos"),
    )
    op.create_index(
        "ix_asset_derivatives_parent_asset_id", "asset_derivatives", ["parent_asset_id"]
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("case_code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("status_rationale", sa.Text(), nullable=False),
        sa.Column("area_geometry", GeographyType("GEOMETRY", 4326), nullable=True),
        sa.Column("public_geometry", GeographyType("GEOMETRY", 4326), nullable=True),
        sa.Column("area_reference", sa.String(length=200), nullable=True),
        sa.Column(
            "lead_investigator_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("investigation_questions", sa.JSON(), nullable=False),
        sa.Column("competing_hypotheses", sa.JSON(), nullable=False),
        sa.Column("evidence_gaps", sa.JSON(), nullable=False),
        sa.Column("referral_record", sa.JSON(), nullable=True),
        sa.Column("field_record_reference", sa.String(length=200), nullable=True),
        sa.Column(
            "specialist_approval_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "authority_approval_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "merged_into_case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True
        ),
        sa.Column("access_class", sa.String(length=32), nullable=False),
        sa.Column(
            "is_public_summary_approved", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("public_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cases_organisation_id", "cases", ["organisation_id"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_lead_investigator_id", "cases", ["lead_investigator_id"])
    if isPostgres:
        op.execute("CREATE INDEX ix_cases_area_geometry_gist ON cases USING GIST (area_geometry)")
        op.execute(
            "CREATE INDEX ix_cases_public_geometry_gist ON cases USING GIST (public_geometry)"
        )

    op.create_table(
        "case_observations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column("link_rationale", sa.Text(), nullable=False),
        sa.Column("proposed_by_type", sa.String(length=32), nullable=False),
        sa.Column(
            "proposed_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column(
            "reviewed_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_contested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("contested_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "observation_id", name="uq_case_observations_case_obs"),
    )
    op.create_index("ix_case_observations_case_id", "case_observations", ["case_id"])
    op.create_index("ix_case_observations_observation_id", "case_observations", ["observation_id"])

    op.create_table(
        "clarification_requests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("observation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organisation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "requested_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("recipient_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("delivery_channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_clarification_requests_observation_id", "clarification_requests", ["observation_id"]
    )
    op.create_index(
        "ix_clarification_requests_organisation_id", "clarification_requests", ["organisation_id"]
    )
    op.create_index(
        "ix_clarification_requests_requested_by_user_id",
        "clarification_requests",
        ["requested_by_user_id"],
    )
    op.create_index(
        "ix_clarification_requests_recipient_user_id",
        "clarification_requests",
        ["recipient_user_id"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organisation_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_organisation_id", "notifications", ["organisation_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts >= 0", name="ck_processing_jobs_attempts_nonneg"),
        sa.CheckConstraint("max_attempts >= 1", name="ck_processing_jobs_max_attempts_pos"),
    )
    op.create_index("ix_processing_jobs_job_type", "processing_jobs", ["job_type"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_available_at", "processing_jobs", ["available_at"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("notifications")
    op.drop_table("clarification_requests")
    op.drop_table("case_observations")
    op.drop_table("cases")
    op.drop_table("asset_derivatives")
    op.drop_table("evidence_assets")
    op.drop_table("observation_sources")
    op.drop_table("observation_versions")
    op.drop_table("observations")
    op.drop_table("units")
    op.drop_table("methods")
    op.drop_table("audit_events")
    op.drop_table("memberships")
    op.drop_table("organisations")
    op.drop_table("users")
    op.drop_table("rate_limit_buckets")
