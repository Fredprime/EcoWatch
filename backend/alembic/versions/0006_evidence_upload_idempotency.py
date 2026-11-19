"""Phase 2 hardening: idempotency key on evidence uploads.

Revision ID: 0006_evidence_upload_idempotency
Revises: 0005_phase2_embeddings
Create Date: 2026-11-19

A nullable idempotency key lets an offline client retry a media upload after a
lost response and receive the original asset id. The unique constraint is scoped
per observation so a key may be reused for a different observation. Existing
rows keep NULL and remain unaffected.

Rollback note: downgrade drops the column and its constraint only.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_evidence_upload_idempotency"
down_revision: str | Sequence[str] | None = "0005_phase2_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evidence_assets",
        sa.Column("idempotency_key", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_evidence_assets_observation_idempotency",
        "evidence_assets",
        ["observation_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_evidence_assets_observation_idempotency",
        "evidence_assets",
        type_="unique",
    )
    op.drop_column("evidence_assets", "idempotency_key")
