"""SQLAlchemy ORM model for governed controlled-vocabulary terms."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ecowatch.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VocabularyTerm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration-only term under a controlled-vocabulary key.

    Terms are governed configuration. They never classify observations or
    produce findings; no observation module reads this table.
    """

    __tablename__ = "controlled_vocabulary_terms"
    __table_args__ = (
        sa.UniqueConstraint("vocabulary_key", "code", name="uq_controlled_vocabulary_key_code"),
    )

    vocabularyKey: Mapped[str] = mapped_column(
        "vocabulary_key", sa.String(100), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column("code", sa.String(100), nullable=False)
    label: Mapped[str] = mapped_column("label", sa.String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    isActive: Mapped[bool] = mapped_column(
        "is_active", sa.Boolean, nullable=False, default=True, server_default=sa.true()
    )
