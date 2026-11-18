"""Phase 2 correlation: evidence_relationships and observation source references.

Rollback note: downgrade drops only what this revision created. It does not touch
any Phase 1 table other than removing the added `observations.source_ref` column.

Revision ID: 0002_phase2_correlation
Revises: 0001_phase1_initial_schema
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase2_correlation"
down_revision: str | Sequence[str] | None = "0001_phase1_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # `FR-027` (repost / shared-source detection) had no way to identify that two
    # reports derive from one original source. Without it every repost counts as
    # an independent account, which is the exact error correlation exists to avoid.
    op.add_column("observations", sa.Column("source_ref", sa.String(length=512), nullable=True))
    op.create_index("ix_observations_source_ref", "observations", ["source_ref"])

    op.create_table(
        "evidence_relationships",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "observation_a_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column(
            "observation_b_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column("task", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("missing_signals", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("method_version", sa.String(length=32), nullable=False),
        sa.Column("source_independent", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "decided_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "observation_a_id",
            "observation_b_id",
            "task",
            name="uq_evidence_relationships_pair_task",
        ),
        sa.CheckConstraint(
            "observation_a_id < observation_b_id",
            name="ck_evidence_relationships_ordered",
        ),
        sa.CheckConstraint(
            "observation_a_id <> observation_b_id",
            name="ck_evidence_relationships_distinct",
        ),
    )
    op.create_index(
        "ix_evidence_relationships_organisation_id", "evidence_relationships", ["organisation_id"]
    )
    op.create_index(
        "ix_evidence_relationships_observation_a_id", "evidence_relationships", ["observation_a_id"]
    )
    op.create_index(
        "ix_evidence_relationships_observation_b_id", "evidence_relationships", ["observation_b_id"]
    )
    op.create_index("ix_evidence_relationships_status", "evidence_relationships", ["status"])


def downgrade() -> None:
    op.drop_table("evidence_relationships")
    op.drop_index("ix_observations_source_ref", table_name="observations")
    op.drop_column("observations", "source_ref")
