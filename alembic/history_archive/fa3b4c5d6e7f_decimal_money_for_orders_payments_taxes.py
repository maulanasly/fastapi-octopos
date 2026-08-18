"""decimal_money_for_orders_payments_taxes

Revision ID: fa3b4c5d6e7f
Revises: e6f7a8b9c0d1
Create Date: 2026-06-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa3b4c5d6e7f"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("orders"):
        if not _has_column(inspector, "orders", "subtotal_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "subtotal_amount", sa.Numeric(precision=12, scale=2), nullable=True
                ),
            )
        if not _has_column(inspector, "orders", "discount_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "discount_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "taxable_base_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "taxable_base_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "tax_total_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "tax_total_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "grand_total_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "grand_total_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "paid_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "paid_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "change_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "change_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )
        if not _has_column(inspector, "orders", "remaining_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "remaining_amount",
                    sa.Numeric(precision=12, scale=2),
                    nullable=False,
                    server_default="0.0",
                ),
            )

        inspector = sa.inspect(bind)
        with op.batch_alter_table("orders") as batch_op:
            if _has_column(inspector, "orders", "subtotal_amount"):
                batch_op.alter_column(
                    "subtotal_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=True,
                )
            if _has_column(inspector, "orders", "discount_amount"):
                batch_op.alter_column(
                    "discount_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "taxable_base_amount"):
                batch_op.alter_column(
                    "taxable_base_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "tax_total_amount"):
                batch_op.alter_column(
                    "tax_total_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "grand_total_amount"):
                batch_op.alter_column(
                    "grand_total_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "total_amount"):
                batch_op.alter_column(
                    "total_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "paid_amount"):
                batch_op.alter_column(
                    "paid_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "change_amount"):
                batch_op.alter_column(
                    "change_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "orders", "remaining_amount"):
                batch_op.alter_column(
                    "remaining_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )

    inspector = sa.inspect(bind)
    if inspector.has_table("order_items") and _has_column(
        inspector, "order_items", "unit_price"
    ):
        with op.batch_alter_table("order_items") as batch_op:
            batch_op.alter_column(
                "unit_price",
                existing_type=sa.Float(),
                type_=sa.Numeric(precision=12, scale=2),
                existing_nullable=False,
            )

    inspector = sa.inspect(bind)
    if inspector.has_table("payments") and _has_column(inspector, "payments", "amount"):
        with op.batch_alter_table("payments") as batch_op:
            batch_op.alter_column(
                "amount",
                existing_type=sa.Float(),
                type_=sa.Numeric(precision=12, scale=2),
                existing_nullable=False,
            )

    inspector = sa.inspect(bind)
    if inspector.has_table("tax_rules") and _has_column(inspector, "tax_rules", "rate"):
        with op.batch_alter_table("tax_rules") as batch_op:
            batch_op.alter_column(
                "rate",
                existing_type=sa.Float(),
                type_=sa.Numeric(precision=7, scale=4),
                existing_nullable=False,
            )

    inspector = sa.inspect(bind)
    if inspector.has_table("order_tax_lines"):
        with op.batch_alter_table("order_tax_lines") as batch_op:
            if _has_column(inspector, "order_tax_lines", "tax_rate"):
                batch_op.alter_column(
                    "tax_rate",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=7, scale=4),
                    existing_nullable=False,
                )
            if _has_column(inspector, "order_tax_lines", "taxable_base"):
                batch_op.alter_column(
                    "taxable_base",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )
            if _has_column(inspector, "order_tax_lines", "tax_amount"):
                batch_op.alter_column(
                    "tax_amount",
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=12, scale=2),
                    existing_nullable=False,
                )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("order_tax_lines") as batch_op:
        batch_op.alter_column(
            "tax_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "taxable_base",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tax_rate",
            existing_type=sa.Numeric(precision=7, scale=4),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table("tax_rules") as batch_op:
        batch_op.alter_column(
            "rate",
            existing_type=sa.Numeric(precision=7, scale=4),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table("payments") as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table("order_items") as batch_op:
        batch_op.alter_column(
            "unit_price",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "remaining_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "change_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "paid_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "total_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "grand_total_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tax_total_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "taxable_base_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "discount_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "subtotal_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            type_=sa.Float(),
            existing_nullable=True,
        )
