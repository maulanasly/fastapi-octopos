"""add_product_replenishment_settings

Revision ID: e7f1a2b3c4d5
Revises: c2d4e6f8a9b0
Create Date: 2026-05-28 00:55:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "c2d4e6f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    product_columns = {column["name"] for column in inspector.get_columns("products")}

    if "min_stock" not in product_columns:
        op.add_column(
            "products",
            sa.Column("min_stock", sa.Integer(), nullable=False, server_default="0"),
        )
    if "max_stock" not in product_columns:
        op.add_column("products", sa.Column("max_stock", sa.Integer(), nullable=True))
    if "reorder_point" not in product_columns:
        op.add_column(
            "products",
            sa.Column(
                "reorder_point", sa.Integer(), nullable=False, server_default="0"
            ),
        )
    if "lead_time_days" not in product_columns:
        op.add_column(
            "products",
            sa.Column(
                "lead_time_days", sa.Integer(), nullable=False, server_default="0"
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    product_columns = {column["name"] for column in inspector.get_columns("products")}

    if "lead_time_days" in product_columns:
        op.drop_column("products", "lead_time_days")
    if "reorder_point" in product_columns:
        op.drop_column("products", "reorder_point")
    if "max_stock" in product_columns:
        op.drop_column("products", "max_stock")
    if "min_stock" in product_columns:
        op.drop_column("products", "min_stock")
