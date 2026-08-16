"""add_product_images_and_category_colors

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-16 21:00:00.000000

Adds products.image_url (served from the /media static mount) and
categories.color (hex) so the POS client can show product pictures and
category-tinted chips.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, Sequence[str], None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("products") and not _has_column(
        inspector, "products", "image_url"
    ):
        op.add_column("products", sa.Column("image_url", sa.String(), nullable=True))

    if inspector.has_table("categories") and not _has_column(
        inspector, "categories", "color"
    ):
        op.add_column("categories", sa.Column("color", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("categories") and _has_column(
        inspector, "categories", "color"
    ):
        op.drop_column("categories", "color")
    if inspector.has_table("products") and _has_column(
        inspector, "products", "image_url"
    ):
        op.drop_column("products", "image_url")
