"""add_drawer_session_id_to_orders

Revision ID: 3c9a8d4f2b11
Revises: 1cbfce1698e4
Create Date: 2026-05-23 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c9a8d4f2b11"
down_revision: str | Sequence[str] | None = "1cbfce1698e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("orders")}

    if "drawer_session_id" not in columns:
        op.add_column(
            "orders", sa.Column("drawer_session_id", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("orders")}

    if "drawer_session_id" in columns:
        op.drop_column("orders", "drawer_session_id")
