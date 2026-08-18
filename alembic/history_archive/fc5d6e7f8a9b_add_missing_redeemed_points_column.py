"""add_missing_redeemed_points_column

Revision ID: fc5d6e7f8a9b
Revises: fb4c5d6e7f8a
Create Date: 2026-06-16 00:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fc5d6e7f8a9b"
down_revision: str | Sequence[str] | None = "fb4c5d6e7f8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("orders") and not _has_column(
        inspector, "orders", "redeemed_points"
    ):
        op.add_column(
            "orders",
            sa.Column(
                "redeemed_points", sa.Integer(), nullable=False, server_default="0"
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("orders") and _has_column(
        inspector, "orders", "redeemed_points"
    ):
        op.drop_column("orders", "redeemed_points")
