"""add_purchase_invoices

Revision ID: f9a1b2c3d4e5
Revises: e7f1a2b3c4d5
Create Date: 2026-05-28 01:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e7f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("purchase_invoices"):
        op.create_table(
            "purchase_invoices",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=False),
            sa.Column("purchase_order_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("invoice_number", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "subtotal_amount", sa.Float(), nullable=False, server_default="0.0"
            ),
            sa.Column("total_amount", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column(
                "variance_amount", sa.Float(), nullable=False, server_default="0.0"
            ),
            sa.Column(
                "has_quantity_variance",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "has_price_variance",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
            sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "supplier_id",
                "invoice_number",
                name="uq_purchase_invoices_supplier_invoice_number",
            ),
        )
        op.create_index(
            op.f("ix_purchase_invoices_id"), "purchase_invoices", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_purchase_invoices_supplier_id"),
            "purchase_invoices",
            ["supplier_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoices_purchase_order_id"),
            "purchase_invoices",
            ["purchase_order_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoices_user_id"),
            "purchase_invoices",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoices_invoice_number"),
            "purchase_invoices",
            ["invoice_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoices_status"),
            "purchase_invoices",
            ["status"],
            unique=False,
        )

    if not inspector.has_table("purchase_invoice_items"):
        op.create_table(
            "purchase_invoice_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("invoice_id", sa.Integer(), nullable=False),
            sa.Column("purchase_order_item_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("billed_quantity", sa.Integer(), nullable=False),
            sa.Column("billed_unit_cost", sa.Float(), nullable=False),
            sa.Column("expected_quantity", sa.Integer(), nullable=False),
            sa.Column("expected_unit_cost", sa.Float(), nullable=False),
            sa.Column(
                "quantity_variance", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "price_variance", sa.Float(), nullable=False, server_default="0.0"
            ),
            sa.Column("line_total", sa.Float(), nullable=False, server_default="0.0"),
            sa.ForeignKeyConstraint(["invoice_id"], ["purchase_invoices.id"]),
            sa.ForeignKeyConstraint(
                ["purchase_order_item_id"], ["purchase_order_items.id"]
            ),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_purchase_invoice_items_id"),
            "purchase_invoice_items",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoice_items_invoice_id"),
            "purchase_invoice_items",
            ["invoice_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoice_items_purchase_order_item_id"),
            "purchase_invoice_items",
            ["purchase_order_item_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_purchase_invoice_items_product_id"),
            "purchase_invoice_items",
            ["product_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("purchase_invoice_items"):
        op.drop_index(
            op.f("ix_purchase_invoice_items_product_id"),
            table_name="purchase_invoice_items",
        )
        op.drop_index(
            op.f("ix_purchase_invoice_items_purchase_order_item_id"),
            table_name="purchase_invoice_items",
        )
        op.drop_index(
            op.f("ix_purchase_invoice_items_invoice_id"),
            table_name="purchase_invoice_items",
        )
        op.drop_index(
            op.f("ix_purchase_invoice_items_id"), table_name="purchase_invoice_items"
        )
        op.drop_table("purchase_invoice_items")

    if inspector.has_table("purchase_invoices"):
        op.drop_index(
            op.f("ix_purchase_invoices_status"), table_name="purchase_invoices"
        )
        op.drop_index(
            op.f("ix_purchase_invoices_invoice_number"), table_name="purchase_invoices"
        )
        op.drop_index(
            op.f("ix_purchase_invoices_user_id"), table_name="purchase_invoices"
        )
        op.drop_index(
            op.f("ix_purchase_invoices_purchase_order_id"),
            table_name="purchase_invoices",
        )
        op.drop_index(
            op.f("ix_purchase_invoices_supplier_id"), table_name="purchase_invoices"
        )
        op.drop_index(op.f("ix_purchase_invoices_id"), table_name="purchase_invoices")
        op.drop_table("purchase_invoices")
