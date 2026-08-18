"""add_user_region

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-16 20:00:00.000000

Adds users.region so each user can pick a regional preset (US/ID) that
overrides the global LocalizationSetting when set.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("users") and not _has_column(inspector, "users", "region"):
        op.add_column("users", sa.Column("region", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("users") and _has_column(inspector, "users", "region"):
        op.drop_column("users", "region")
