"""Reserve the bounded revoked-token purge revision.

Revision ID: 0010_token_revocation_purge
Revises: 0009_case_two_key_governance
Create Date: 2026-11-20

The purge is application-level: the identity service deletes a bounded batch of
expired revoked_tokens rows and records an audit event. No schema change is needed;
this revision keeps the chain linear for the append-only audit migration.
"""

from collections.abc import Sequence

revision: str = "0010_token_revocation_purge"
down_revision: str | Sequence[str] | None = "0009_case_two_key_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No schema change: expiry deletion is implemented in the identity service."""


def downgrade() -> None:
    """No schema change to revert."""
