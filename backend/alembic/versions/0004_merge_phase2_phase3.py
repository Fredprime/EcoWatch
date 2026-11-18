"""Merge the Phase 2 cluster and Phase 3 schema migration branches.

Revision ID: 0004_merge_phase2_phase3
Revises: 0003_phase2_clusters, 0003_phase3_schema
Create Date: 2026-11-18

Both 0003 revisions descend from 0002 and add independent tables, so the merge
is a booking revision only. It gives `alembic upgrade head` one target without
changing either branch's schema.
"""

from collections.abc import Sequence

revision: str = "0004_merge_phase2_phase3"
down_revision: str | Sequence[str] | None = (
    "0003_phase2_clusters",
    "0003_phase3_schema",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
