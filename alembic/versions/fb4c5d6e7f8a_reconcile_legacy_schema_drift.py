"""reconcile_legacy_schema_drift

Revision ID: fb4c5d6e7f8a
Revises: fa3b4c5d6e7f
Create Date: 2026-06-16 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fb4c5d6e7f8a"
down_revision: Union[str, Sequence[str], None] = "fa3b4c5d6e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Orders table compatibility with current ORM model
    if inspector.has_table("orders"):
        if not _has_column(inspector, "orders", "customer_id"):
            op.add_column(
                "orders", sa.Column("customer_id", sa.Integer(), nullable=True)
            )
        if not _has_column(inspector, "orders", "promotion_id"):
            op.add_column(
                "orders", sa.Column("promotion_id", sa.Integer(), nullable=True)
            )
        if not _has_column(inspector, "orders", "idempotency_key"):
            op.add_column(
                "orders", sa.Column("idempotency_key", sa.String(), nullable=True)
            )

    inspector = sa.inspect(bind)
    if inspector.has_table("orders"):
        if _has_column(inspector, "orders", "idempotency_key") and not _has_index(
            inspector, "orders", "ix_orders_idempotency_key"
        ):
            op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])

    # Payments table compatibility with current ORM model
    if inspector.has_table("payments"):
        if not _has_column(inspector, "payments", "user_id"):
            op.add_column("payments", sa.Column("user_id", sa.Integer(), nullable=True))
            op.execute(
                """
                UPDATE payments
                SET user_id = (
                    SELECT orders.user_id
                    FROM orders
                    WHERE orders.id = payments.order_id
                )
                WHERE user_id IS NULL
                """
            )
        if not _has_column(inspector, "payments", "idempotency_key"):
            op.add_column(
                "payments", sa.Column("idempotency_key", sa.String(), nullable=True)
            )

    inspector = sa.inspect(bind)
    if inspector.has_table("payments"):
        if _has_column(inspector, "payments", "user_id") and not _has_index(
            inspector, "payments", "ix_payments_user_id"
        ):
            op.create_index("ix_payments_user_id", "payments", ["user_id"])
        if _has_column(inspector, "payments", "idempotency_key") and not _has_index(
            inspector, "payments", "ix_payments_idempotency_key"
        ):
            op.create_index(
                "ix_payments_idempotency_key", "payments", ["idempotency_key"]
            )

    # Refunds table compatibility with current ORM model
    if inspector.has_table("refunds"):
        if not _has_column(inspector, "refunds", "order_id"):
            op.add_column("refunds", sa.Column("order_id", sa.Integer(), nullable=True))
        if not _has_column(inspector, "refunds", "user_id"):
            op.add_column("refunds", sa.Column("user_id", sa.Integer(), nullable=True))
        if not _has_column(inspector, "refunds", "idempotency_key"):
            op.add_column(
                "refunds", sa.Column("idempotency_key", sa.String(), nullable=True)
            )
        if not _has_column(inspector, "refunds", "reason"):
            op.add_column("refunds", sa.Column("reason", sa.Text(), nullable=True))
        if not _has_column(inspector, "refunds", "total_amount"):
            op.add_column(
                "refunds", sa.Column("total_amount", sa.Float(), nullable=True)
            )
            if _has_column(inspector, "refunds", "amount"):
                op.execute(
                    """
                    UPDATE refunds
                    SET total_amount = amount
                    WHERE total_amount IS NULL
                    """
                )

    inspector = sa.inspect(bind)
    if inspector.has_table("refunds"):
        if _has_column(inspector, "refunds", "idempotency_key") and not _has_index(
            inspector, "refunds", "ix_refunds_idempotency_key"
        ):
            op.create_index(
                "ix_refunds_idempotency_key", "refunds", ["idempotency_key"]
            )


def downgrade() -> None:
    """Downgrade schema."""
    # Intentionally no-op for safety in legacy reconciliation migration.
    pass
