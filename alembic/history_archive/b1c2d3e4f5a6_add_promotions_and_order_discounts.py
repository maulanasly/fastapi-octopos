"""add_promotions_and_order_discounts

Revision ID: b1c2d3e4f5a6
Revises: 9d4e2b1c7a8f
Create Date: 2026-05-28 01:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "9d4e2b1c7a8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("promotions"):
        op.create_table(
            "promotions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("discount_type", sa.String(), nullable=False),
            sa.Column("discount_value", sa.Float(), nullable=False),
            sa.Column("min_order_amount", sa.Float(), nullable=False),
            sa.Column("max_discount_amount", sa.Float(), nullable=True),
            sa.Column("applies_to", sa.String(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("category_id", sa.Integer(), nullable=True),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("usage_limit", sa.Integer(), nullable=True),
            sa.Column("usage_count", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_promotions_id"), "promotions", ["id"], unique=False)
        op.create_index(op.f("ix_promotions_code"), "promotions", ["code"], unique=True)

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "promotion_id" not in order_columns:
        op.add_column("orders", sa.Column("promotion_id", sa.Integer(), nullable=True))
    if "subtotal_amount" not in order_columns:
        op.add_column("orders", sa.Column("subtotal_amount", sa.Float(), nullable=True))
    if "discount_amount" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "discount_amount", sa.Float(), nullable=False, server_default="0.0"
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "discount_amount" in order_columns:
        op.drop_column("orders", "discount_amount")
    if "subtotal_amount" in order_columns:
        op.drop_column("orders", "subtotal_amount")
    if "promotion_id" in order_columns:
        op.drop_column("orders", "promotion_id")

    if inspector.has_table("promotions"):
        op.drop_index(op.f("ix_promotions_code"), table_name="promotions")
        op.drop_index(op.f("ix_promotions_id"), table_name="promotions")
        op.drop_table("promotions")
