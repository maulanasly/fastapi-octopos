"""add_order_serving_status

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-17 15:00:00.000000

Orders gain a serving queue for kitchen/prep display: ``serving_status``
(``none`` -> ``queued`` -> ``preparing`` -> ``ready`` -> ``served``) plus
timestamps for each stage so reports can measure prep time. Fully paid
orders are queued automatically; cancelled orders fall out of the queue
query. Portable across PostgreSQL (direct DDL) and SQLite (batch mode).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = [
    sa.Column("serving_status", sa.String(), nullable=False, server_default="none"),
    sa.Column("preparing_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("served_at", sa.DateTime(timezone=True), nullable=True),
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("orders"):
        return
    existing = {c["name"] for c in inspector.get_columns("orders")}
    to_add = [c for c in _COLUMNS if c.name not in existing]
    if not to_add:
        return
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("orders") as batch_op:
            for column in to_add:
                batch_op.add_column(column)
    else:
        for column in to_add:
            op.add_column("orders", column)

    index_name = "ix_orders_serving_status"
    table_indexes = {i["name"] for i in inspector.get_indexes("orders")}
    if index_name not in table_indexes:
        op.create_index(index_name, "orders", ["serving_status"])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("orders"):
        return

    index_name = "ix_orders_serving_status"
    table_indexes = {i["name"] for i in inspector.get_indexes("orders")}
    if index_name in table_indexes:
        op.drop_index(index_name, table_name="orders")

    existing = {c["name"] for c in inspector.get_columns("orders")}
    to_drop = [c for c in reversed(_COLUMNS) if c.name in existing]
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("orders") as batch_op:
            for column in to_drop:
                batch_op.drop_column(column.name)
    else:
        for column in to_drop:
            op.drop_column("orders", column.name)
