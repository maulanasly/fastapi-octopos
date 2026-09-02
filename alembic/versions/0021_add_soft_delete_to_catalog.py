"""add soft delete to catalog

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-02 23:00:00.000000

Adds deleted_at for soft-delete sync (offline ghost fix).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021"
down_revision: str | Sequence[str] | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("categories") and not _has_column(
        inspector, "categories", "deleted_at"
    ):
        op.add_column(
            "categories",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_categories_deleted_at", "categories", ["deleted_at"])

    if inspector.has_table("products") and not _has_column(
        inspector, "products", "deleted_at"
    ):
        op.add_column(
            "products",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_products_deleted_at", "products", ["deleted_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("products") and _has_column(
        inspector, "products", "deleted_at"
    ):
        op.drop_index("ix_products_deleted_at", table_name="products")
        op.drop_column("products", "deleted_at")

    if inspector.has_table("categories") and _has_column(
        inspector, "categories", "deleted_at"
    ):
        op.drop_index("ix_categories_deleted_at", table_name="categories")
        op.drop_column("categories", "deleted_at")
