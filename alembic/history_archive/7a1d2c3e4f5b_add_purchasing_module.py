"""add_purchasing_module

Revision ID: 7a1d2c3e4f5b
Revises: 4b2d6f1a9c3e
Create Date: 2026-05-28 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1d2c3e4f5b"
down_revision: Union[str, Sequence[str], None] = "4b2d6f1a9c3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("suppliers"):
        op.create_table(
            "suppliers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("contact_email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_suppliers_id"), "suppliers", ["id"], unique=False)
        op.create_index(op.f("ix_suppliers_name"), "suppliers", ["name"], unique=False)

    if not inspector.has_table("purchase_orders"):
        op.create_table(
            "purchase_orders",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("total_estimated_amount", sa.Float(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_purchase_orders_id"), "purchase_orders", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_purchase_orders_status"),
            "purchase_orders",
            ["status"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_orders_supplier_id"),
            "purchase_orders",
            ["supplier_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_orders_user_id"),
            "purchase_orders",
            ["user_id"],
            unique=False,
        )

    if not inspector.has_table("purchase_order_items"):
        op.create_table(
            "purchase_order_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("purchase_order_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("quantity_ordered", sa.Integer(), nullable=False),
            sa.Column("quantity_received", sa.Integer(), nullable=False),
            sa.Column("unit_cost", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_purchase_order_items_id"),
            "purchase_order_items",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_order_items_product_id"),
            "purchase_order_items",
            ["product_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_order_items_purchase_order_id"),
            "purchase_order_items",
            ["purchase_order_id"],
            unique=False,
        )

    stock_movement_columns = {
        column["name"] for column in inspector.get_columns("stock_movements")
    }
    if "purchase_order_id" not in stock_movement_columns:
        op.add_column(
            "stock_movements",
            sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        )
    stock_movement_indexes = {
        index["name"] for index in inspector.get_indexes("stock_movements")
    }
    if op.f("ix_stock_movements_purchase_order_id") not in stock_movement_indexes:
        op.create_index(
            op.f("ix_stock_movements_purchase_order_id"),
            "stock_movements",
            ["purchase_order_id"],
            unique=False,
        )

    if "purchase_order_item_id" not in stock_movement_columns:
        op.add_column(
            "stock_movements",
            sa.Column("purchase_order_item_id", sa.Integer(), nullable=True),
        )
    stock_movement_indexes = {
        index["name"] for index in inspector.get_indexes("stock_movements")
    }
    if op.f("ix_stock_movements_purchase_order_item_id") not in stock_movement_indexes:
        op.create_index(
            op.f("ix_stock_movements_purchase_order_item_id"),
            "stock_movements",
            ["purchase_order_item_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    stock_movement_columns = {
        column["name"] for column in inspector.get_columns("stock_movements")
    }
    if "purchase_order_item_id" in stock_movement_columns:
        op.drop_index(
            op.f("ix_stock_movements_purchase_order_item_id"),
            table_name="stock_movements",
        )
        op.drop_column("stock_movements", "purchase_order_item_id")

    if "purchase_order_id" in stock_movement_columns:
        op.drop_index(
            op.f("ix_stock_movements_purchase_order_id"), table_name="stock_movements"
        )
        op.drop_column("stock_movements", "purchase_order_id")

    if inspector.has_table("purchase_order_items"):
        op.drop_index(
            op.f("ix_purchase_order_items_purchase_order_id"),
            table_name="purchase_order_items",
        )
        op.drop_index(
            op.f("ix_purchase_order_items_product_id"),
            table_name="purchase_order_items",
        )
        op.drop_index(
            op.f("ix_purchase_order_items_id"), table_name="purchase_order_items"
        )
        op.drop_table("purchase_order_items")

    if inspector.has_table("purchase_orders"):
        op.drop_index(op.f("ix_purchase_orders_user_id"), table_name="purchase_orders")
        op.drop_index(
            op.f("ix_purchase_orders_supplier_id"), table_name="purchase_orders"
        )
        op.drop_index(op.f("ix_purchase_orders_status"), table_name="purchase_orders")
        op.drop_index(op.f("ix_purchase_orders_id"), table_name="purchase_orders")
        op.drop_table("purchase_orders")

    if inspector.has_table("suppliers"):
        op.drop_index(op.f("ix_suppliers_name"), table_name="suppliers")
        op.drop_index(op.f("ix_suppliers_id"), table_name="suppliers")
        op.drop_table("suppliers")
