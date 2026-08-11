"""add_stock_movements_table

Revision ID: 4b2d6f1a9c3e
Revises: 9f4d0e7c1b2a
Create Date: 2026-05-27 23:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b2d6f1a9c3e"
down_revision: Union[str, Sequence[str], None] = "9f4d0e7c1b2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("stock_movements"):
        op.create_table(
            "stock_movements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("order_id", sa.Integer(), nullable=True),
            sa.Column("order_item_id", sa.Integer(), nullable=True),
            sa.Column("refund_id", sa.Integer(), nullable=True),
            sa.Column("movement_type", sa.String(), nullable=False),
            sa.Column("quantity_before", sa.Integer(), nullable=False),
            sa.Column("quantity_delta", sa.Integer(), nullable=False),
            sa.Column("quantity_after", sa.Integer(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["refund_id"], ["refunds.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_stock_movements_id"), "stock_movements", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_stock_movements_product_id"),
            "stock_movements",
            ["product_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_stock_movements_user_id"),
            "stock_movements",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_stock_movements_order_id"),
            "stock_movements",
            ["order_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_stock_movements_order_item_id"),
            "stock_movements",
            ["order_item_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_stock_movements_refund_id"),
            "stock_movements",
            ["refund_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_stock_movements_movement_type"),
            "stock_movements",
            ["movement_type"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("stock_movements"):
        op.drop_index(
            op.f("ix_stock_movements_movement_type"), table_name="stock_movements"
        )
        op.drop_index(
            op.f("ix_stock_movements_refund_id"), table_name="stock_movements"
        )
        op.drop_index(
            op.f("ix_stock_movements_order_item_id"), table_name="stock_movements"
        )
        op.drop_index(op.f("ix_stock_movements_order_id"), table_name="stock_movements")
        op.drop_index(op.f("ix_stock_movements_user_id"), table_name="stock_movements")
        op.drop_index(
            op.f("ix_stock_movements_product_id"), table_name="stock_movements"
        )
        op.drop_index(op.f("ix_stock_movements_id"), table_name="stock_movements")
        op.drop_table("stock_movements")
