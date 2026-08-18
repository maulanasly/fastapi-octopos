"""add_order_payment_settlement_fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-28 02:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}

    if "paid_amount" not in order_columns:
        op.add_column(
            "orders",
            sa.Column("paid_amount", sa.Float(), nullable=False, server_default="0.0"),
        )
    if "change_amount" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "change_amount", sa.Float(), nullable=False, server_default="0.0"
            ),
        )
    if "remaining_amount" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "remaining_amount", sa.Float(), nullable=False, server_default="0.0"
            ),
        )

    op.execute(
        """
        UPDATE orders
        SET
            paid_amount = MIN(
                COALESCE(total_amount, 0.0),
                COALESCE((SELECT SUM(amount) FROM payments WHERE payments.order_id = orders.id), 0.0)
            ),
            change_amount = MAX(
                COALESCE((SELECT SUM(amount) FROM payments WHERE payments.order_id = orders.id), 0.0)
                - COALESCE(total_amount, 0.0),
                0.0
            ),
            remaining_amount = MAX(
                COALESCE(total_amount, 0.0) - MIN(
                    COALESCE(total_amount, 0.0),
                    COALESCE((SELECT SUM(amount) FROM payments WHERE payments.order_id = orders.id), 0.0)
                ),
                0.0
            )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}

    if "remaining_amount" in order_columns:
        op.drop_column("orders", "remaining_amount")
    if "change_amount" in order_columns:
        op.drop_column("orders", "change_amount")
    if "paid_amount" in order_columns:
        op.drop_column("orders", "paid_amount")
