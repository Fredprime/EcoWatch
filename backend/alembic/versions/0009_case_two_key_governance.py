"""Record the two-key human approval for case field verification.

Revision ID: 0009_case_two_key_governance
Revises: 0008_two_key_governance
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_case_two_key_governance"
down_revision: str | Sequence[str] | None = "0008_two_key_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column(
            "specialist_approver_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "authority_approver_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "cases",
        sa.Column("two_key_approved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "two_key_approved_at")
    op.drop_column("cases", "authority_approver_user_id")
    op.drop_column("cases", "specialist_approver_user_id")
