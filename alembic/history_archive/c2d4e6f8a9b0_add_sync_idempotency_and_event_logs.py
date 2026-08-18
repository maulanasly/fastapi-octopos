"""add_sync_idempotency_and_event_logs

Revision ID: c2d4e6f8a9b0
Revises: b1c2d3e4f5a6
Create Date: 2026-05-28 03:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d4e6f8a9b0"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(
        index["name"] == index_name for index in inspector.get_indexes(table_name)
    )


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "idempotency_key" not in order_columns:
        op.add_column(
            "orders", sa.Column("idempotency_key", sa.String(), nullable=True)
        )
    if not _has_index(inspector, "orders", "ix_orders_idempotency_key"):
        op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])
    if not _has_index(inspector, "orders", "uq_orders_user_idempotency"):
        op.create_index(
            "uq_orders_user_idempotency",
            "orders",
            ["user_id", "idempotency_key"],
            unique=True,
        )

    payment_columns = {column["name"] for column in inspector.get_columns("payments")}
    if "user_id" not in payment_columns:
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
    if "idempotency_key" not in payment_columns:
        op.add_column(
            "payments", sa.Column("idempotency_key", sa.String(), nullable=True)
        )
    if not _has_index(inspector, "payments", "ix_payments_user_id"):
        op.create_index("ix_payments_user_id", "payments", ["user_id"])
    if not _has_index(inspector, "payments", "ix_payments_idempotency_key"):
        op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"])
    if not _has_index(inspector, "payments", "uq_payments_user_idempotency"):
        op.create_index(
            "uq_payments_user_idempotency",
            "payments",
            ["user_id", "idempotency_key"],
            unique=True,
        )

    refund_columns = {column["name"] for column in inspector.get_columns("refunds")}
    if "idempotency_key" not in refund_columns:
        op.add_column(
            "refunds", sa.Column("idempotency_key", sa.String(), nullable=True)
        )
    if not _has_index(inspector, "refunds", "ix_refunds_idempotency_key"):
        op.create_index("ix_refunds_idempotency_key", "refunds", ["idempotency_key"])
    if not _has_index(inspector, "refunds", "uq_refunds_user_idempotency"):
        op.create_index(
            "uq_refunds_user_idempotency",
            "refunds",
            ["user_id", "idempotency_key"],
            unique=True,
        )

    if not inspector.has_table("sync_event_logs"):
        op.create_table(
            "sync_event_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("client_event_id", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("idempotency_key", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("resource_type", sa.String(), nullable=True),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column(
                "processed_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "client_event_id",
                "event_type",
                name="uq_sync_event_log_unique",
            ),
        )
        op.create_index(
            op.f("ix_sync_event_logs_id"), "sync_event_logs", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_sync_event_logs_user_id"),
            "sync_event_logs",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_sync_event_logs_client_event_id"),
            "sync_event_logs",
            ["client_event_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_sync_event_logs_event_type"),
            "sync_event_logs",
            ["event_type"],
            unique=False,
        )
        op.create_index(
            op.f("ix_sync_event_logs_idempotency_key"),
            "sync_event_logs",
            ["idempotency_key"],
            unique=False,
        )
        op.create_index(
            op.f("ix_sync_event_logs_status"),
            "sync_event_logs",
            ["status"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("sync_event_logs"):
        op.drop_index(op.f("ix_sync_event_logs_status"), table_name="sync_event_logs")
        op.drop_index(
            op.f("ix_sync_event_logs_idempotency_key"), table_name="sync_event_logs"
        )
        op.drop_index(
            op.f("ix_sync_event_logs_event_type"), table_name="sync_event_logs"
        )
        op.drop_index(
            op.f("ix_sync_event_logs_client_event_id"), table_name="sync_event_logs"
        )
        op.drop_index(op.f("ix_sync_event_logs_user_id"), table_name="sync_event_logs")
        op.drop_index(op.f("ix_sync_event_logs_id"), table_name="sync_event_logs")
        op.drop_table("sync_event_logs")

    if _has_index(inspector, "refunds", "uq_refunds_user_idempotency"):
        op.drop_index("uq_refunds_user_idempotency", table_name="refunds")
    if _has_index(inspector, "refunds", "ix_refunds_idempotency_key"):
        op.drop_index("ix_refunds_idempotency_key", table_name="refunds")
    refund_columns = {column["name"] for column in inspector.get_columns("refunds")}
    if "idempotency_key" in refund_columns:
        op.drop_column("refunds", "idempotency_key")

    if _has_index(inspector, "payments", "uq_payments_user_idempotency"):
        op.drop_index("uq_payments_user_idempotency", table_name="payments")
    if _has_index(inspector, "payments", "ix_payments_idempotency_key"):
        op.drop_index("ix_payments_idempotency_key", table_name="payments")
    if _has_index(inspector, "payments", "ix_payments_user_id"):
        op.drop_index("ix_payments_user_id", table_name="payments")
    payment_columns = {column["name"] for column in inspector.get_columns("payments")}
    if "idempotency_key" in payment_columns:
        op.drop_column("payments", "idempotency_key")
    if "user_id" in payment_columns:
        op.drop_column("payments", "user_id")

    if _has_index(inspector, "orders", "uq_orders_user_idempotency"):
        op.drop_index("uq_orders_user_idempotency", table_name="orders")
    if _has_index(inspector, "orders", "ix_orders_idempotency_key"):
        op.drop_index("ix_orders_idempotency_key", table_name="orders")
    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "idempotency_key" in order_columns:
        op.drop_column("orders", "idempotency_key")
