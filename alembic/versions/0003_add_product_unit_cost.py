"""add_product_unit_cost

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-12 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("products") and not _has_column(
        inspector, "products", "unit_cost"
    ):
        op.add_column(
            "products",
            sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("products") and _has_column(
        inspector, "products", "unit_cost"
    ):
        op.drop_column("products", "unit_cost")
