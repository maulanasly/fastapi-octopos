"""add_updated_at_for_catalog_sync

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-16 10:30:00.000000

Adds updated_at to products, categories, and promotions so offline
terminals can pull delta catalog changes via /sync/catalog?since=.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


_TABLES = ("products", "categories", "promotions")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in _TABLES:
        if inspector.has_table(table) and not _has_column(
            inspector, table, "updated_at"
        ):
            op.add_column(
                table,
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in _TABLES:
        if inspector.has_table(table) and _has_column(inspector, table, "updated_at"):
            op.drop_column(table, "updated_at")
