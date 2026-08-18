"""add_order_reservation_fields

Revision ID: a1b2c3d4e5f6
Revises: f9a1b2c3d4e5
Create Date: 2026-05-28 01:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f9a1b2c3d4e5"
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

    if "reservation_status" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "reservation_status",
                sa.String(),
                nullable=False,
                server_default="reserved",
            ),
        )
    if "reservation_expires_at" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "reservation_expires_at", sa.DateTime(timezone=True), nullable=True
            ),
        )

    if not _has_index(inspector, "orders", "ix_orders_reservation_status"):
        op.create_index(
            "ix_orders_reservation_status",
            "orders",
            ["reservation_status"],
            unique=False,
        )
    if not _has_index(inspector, "orders", "ix_orders_reservation_expires_at"):
        op.create_index(
            "ix_orders_reservation_expires_at",
            "orders",
            ["reservation_expires_at"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}

    if _has_index(inspector, "orders", "ix_orders_reservation_expires_at"):
        op.drop_index("ix_orders_reservation_expires_at", table_name="orders")
    if _has_index(inspector, "orders", "ix_orders_reservation_status"):
        op.drop_index("ix_orders_reservation_status", table_name="orders")

    if "reservation_expires_at" in order_columns:
        op.drop_column("orders", "reservation_expires_at")
    if "reservation_status" in order_columns:
        op.drop_column("orders", "reservation_status")
