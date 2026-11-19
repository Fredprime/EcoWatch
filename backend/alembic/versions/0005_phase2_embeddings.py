"""Phase 2 correlation: pgvector-backed text embeddings.

Revision ID: 0005_phase2_embeddings
Revises: 0004_merge_phase2_phase3
Create Date: 2026-11-18

One row per (observation, model version, input hash) makes an unchanged report
skip re-embedding on rescan. The vector index is created only on PostgreSQL;
SQLite is the test dialect and has no pgvector equivalent.

Rollback note: downgrade drops this table and its indexes only. It deliberately
leaves the `vector` extension installed because extensions are shared database
objects and the extension may be used by another migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from ecowatch.core.vector import VectorType
from ecowatch.modules.correlation.embeddings import VECTOR_DIMENSIONS

revision: str = "0005_phase2_embeddings"
down_revision: str | Sequence[str] | None = "0004_merge_phase2_phase3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    isPostgres = bind.dialect.name == "postgresql"
    # ADR-030: pgvector lives in the same PostgreSQL service as PostGIS.
    if isPostgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "correlation_embeddings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id"),
            nullable=False,
        ),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", VectorType(VECTOR_DIMENSIONS), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "observation_id",
            "model_version",
            "input_hash",
            name="uq_correlation_embeddings_observation_model_input",
        ),
    )
    op.create_index(
        "ix_correlation_embeddings_organisation_id",
        "correlation_embeddings",
        ["organisation_id"],
    )
    op.create_index(
        "ix_correlation_embeddings_observation_id",
        "correlation_embeddings",
        ["observation_id"],
    )
    op.create_index(
        "ix_correlation_embeddings_model_input",
        "correlation_embeddings",
        ["model_version", "input_hash"],
    )
    if isPostgres:
        # Cosine distance is the bounded semantic candidate prefilter. HNSW needs
        # no training set, so it can be built on an empty prototype database.
        op.execute(
            "CREATE INDEX ix_correlation_embeddings_vector "
            "ON correlation_embeddings USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_correlation_embeddings_vector")
    op.drop_table("correlation_embeddings")
