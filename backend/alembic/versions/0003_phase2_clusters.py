"""Phase 2 correlation: provisional clusters and the tie flag.

Revision ID: 0003_phase2_clusters
Revises: 0002_phase2_correlation
Create Date: 2026-11-18

`correlation_clusters` is a container for staff to look at, not a case. Nothing
here links a cluster to a case: promotion is a separate audited action, and it
is not built.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase2_clusters"
down_revision: str | Sequence[str] | None = "0002_phase2_correlation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A tie is a fact about the scan, not a ranking decision the engine may make
    # quietly, so it has to survive the request that produced it.
    op.add_column(
        "evidence_relationships",
        sa.Column("ambiguous", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "correlation_clusters",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_correlation_clusters_organisation_id", "correlation_clusters", ["organisation_id"]
    )

    op.create_table(
        "correlation_cluster_members",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "cluster_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("correlation_clusters.id"),
            nullable=False,
        ),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # One cluster per report: A~B and B~C must not become one cluster.
        sa.UniqueConstraint(
            "observation_id", name="uq_correlation_cluster_members_observation"
        ),
    )
    op.create_index(
        "ix_correlation_cluster_members_cluster_id", "correlation_cluster_members", ["cluster_id"]
    )
    op.create_index(
        "ix_correlation_cluster_members_observation_id",
        "correlation_cluster_members",
        ["observation_id"],
    )


def downgrade() -> None:
    op.drop_table("correlation_cluster_members")
    op.drop_table("correlation_clusters")
    op.drop_column("evidence_relationships", "ambiguous")
