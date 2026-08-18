"""add_query_indexes

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-17 10:00:00.000000

Adds indexes on the hot FK and status columns used by cashier lists,
reports, refunds, reservation sweeps and inventory range filters, so
queries stop scanning tables as the POS dataset grows.

Index names follow the SQLAlchemy ``ix_<table>_<column>`` convention so
model metadata and the real schema stay in sync.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, column) pairs — every new index mirrors index=True on the model.
_INDEXES = [
    ("orders", "user_id"),
    ("orders", "customer_id"),
    ("orders", "promotion_id"),
    ("orders", "drawer_session_id"),
    ("orders", "status"),
    ("order_items", "order_id"),
    ("order_items", "product_id"),
    ("payments", "order_id"),
    ("refunds", "order_id"),
    ("refunds", "user_id"),
    ("refund_items", "refund_id"),
    ("refund_items", "order_item_id"),
    ("refund_items", "product_id"),
    ("products", "category_id"),
    ("drawer_sessions", "user_id"),
    ("refresh_tokens", "user_id"),
    ("promotions", "product_id"),
    ("promotions", "category_id"),
    ("stock_movements", "created_at"),
]


def upgrade() -> None:
    """Upgrade schema."""
    import sqlalchemy as sa

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, column in _INDEXES:
        if not inspector.has_table(table):
            continue
        index_name = f"ix_{table}_{column}"
        table_indexes = {i["name"] for i in inspector.get_indexes(table)}
        if index_name not in table_indexes:
            op.create_index(index_name, table, [column])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    import sqlalchemy as sa

    inspector = sa.inspect(bind)
    for table, column in reversed(_INDEXES):
        if not inspector.has_table(table):
            continue
        index_name = f"ix_{table}_{column}"
        table_indexes = {i["name"] for i in inspector.get_indexes(table)}
        if index_name in table_indexes:
            op.drop_index(index_name, table_name=table)
