"""Add governed controlled-vocabulary terms.

Revision ID: 0012_controlled_vocabularies
Revises: 0011_audit_append_only
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_controlled_vocabularies"
down_revision: str | Sequence[str] | None = "0011_audit_append_only"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "controlled_vocabulary_terms",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("vocabulary_key", sa.String(100), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("vocabulary_key", "code", name="uq_controlled_vocabulary_key_code"),
    )
    op.create_index(
        "ix_controlled_vocabulary_terms_vocabulary_key",
        "controlled_vocabulary_terms",
        ["vocabulary_key"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_controlled_vocabulary_terms_vocabulary_key",
        table_name="controlled_vocabulary_terms",
    )
    op.drop_table("controlled_vocabulary_terms")
