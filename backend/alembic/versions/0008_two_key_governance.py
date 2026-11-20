"""Record proposer and two-key approvers for governance decisions.

Revision ID: 0008_two_key_governance
Revises: 0007_token_revocation
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_two_key_governance"
down_revision: str | Sequence[str] | None = "0007_token_revocation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interventions",
        sa.Column(
            "proposed_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
    )
    for table in ("verification_assessments", "publications"):
        op.add_column(
            table,
            sa.Column(
                "specialist_approver_user_id",
                sa.Uuid(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
        )
        op.add_column(
            table,
            sa.Column(
                "authority_approver_user_id",
                sa.Uuid(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
        )
        op.add_column(
            table,
            sa.Column("two_key_approved_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    for table in ("verification_assessments", "publications"):
        op.drop_column(table, "two_key_approved_at")
        op.drop_column(table, "authority_approver_user_id")
        op.drop_column(table, "specialist_approver_user_id")
    op.drop_column("interventions", "proposed_by_user_id")
