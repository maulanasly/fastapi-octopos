"""add_refunds_tables

Revision ID: 9f4d0e7c1b2a
Revises: 3c9a8d4f2b11
Create Date: 2026-05-27 23:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f4d0e7c1b2a"
down_revision: str | Sequence[str] | None = "3c9a8d4f2b11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("refunds"):
        op.create_table(
            "refunds",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("total_amount", sa.Float(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_refunds_id"), "refunds", ["id"], unique=False)

    if not inspector.has_table("refund_items"):
        op.create_table(
            "refund_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("refund_id", sa.Integer(), nullable=False),
            sa.Column("order_item_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["refund_id"], ["refunds.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_refund_items_id"), "refund_items", ["id"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("refund_items"):
        op.drop_index(op.f("ix_refund_items_id"), table_name="refund_items")
        op.drop_table("refund_items")

    if inspector.has_table("refunds"):
        op.drop_index(op.f("ix_refunds_id"), table_name="refunds")
        op.drop_table("refunds")
