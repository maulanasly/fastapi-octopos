"""add_login_lockout_columns

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-16 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("users") and not _has_column(
        inspector, "users", "failed_login_attempts"
    ):
        op.add_column(
            "users",
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        )
    if inspector.has_table("users") and not _has_column(
        inspector, "users", "locked_until"
    ):
        op.add_column(
            "users",
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("users") and _has_column(inspector, "users", "locked_until"):
        op.drop_column("users", "locked_until")
    if inspector.has_table("users") and _has_column(
        inspector, "users", "failed_login_attempts"
    ):
        op.drop_column("users", "failed_login_attempts")
