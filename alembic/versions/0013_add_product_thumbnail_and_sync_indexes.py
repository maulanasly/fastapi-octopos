"""add_product_thumbnail_and_sync_indexes

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-17 14:00:00.000000

Product photos gain a downscaled WebP ``thumbnail_url`` for bandwidth-
friendly mobile catalog grids. The catalog delta-sync queries
(``updated_at > since``) and order date-range filters get indexes so
they stop scanning tables as the POS dataset grows.

Index names follow the SQLAlchemy ``ix_<table>_<column>`` convention so
model metadata and the real schema stay in sync. Portable across
PostgreSQL (direct DDL) and SQLite (batch mode).
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column) pairs — every new index mirrors index=True on the model.
_SYNC_INDEXES = [
    ("products", "updated_at"),
    ("categories", "updated_at"),
    ("promotions", "updated_at"),
    ("tax_rules", "updated_at"),
    ("orders", "created_at"),
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("products") and not any(
        c["name"] == "thumbnail_url" for c in inspector.get_columns("products")
    ):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("products") as batch_op:
                batch_op.add_column(
                    sa.Column("thumbnail_url", sa.String(), nullable=True)
                )
        else:
            op.add_column(
                "products", sa.Column("thumbnail_url", sa.String(), nullable=True)
            )

    for table, column in _SYNC_INDEXES:
        if not inspector.has_table(table):
            continue
        index_name = f"ix_{table}_{column}"
        table_indexes = {i["name"] for i in inspector.get_indexes(table)}
        if index_name not in table_indexes:
            op.create_index(index_name, table, [column])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, column in reversed(_SYNC_INDEXES):
        if not inspector.has_table(table):
            continue
        index_name = f"ix_{table}_{column}"
        table_indexes = {i["name"] for i in inspector.get_indexes(table)}
        if index_name in table_indexes:
            op.drop_index(index_name, table_name=table)

    if inspector.has_table("products") and any(
        c["name"] == "thumbnail_url" for c in inspector.get_columns("products")
    ):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("products") as batch_op:
                batch_op.drop_column("thumbnail_url")
        else:
            op.drop_column("products", "thumbnail_url")
