"""add_order_item_unit_cost

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-21 16:00:00.000000

Snapshots the product cost onto each sold line so COGS can be reported
per sale. Nullable: orders created before this migration have no cost
snapshot and are excluded from margin math (surfaced as partial
coverage in the sales summary).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: str | Sequence[str] | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("order_items") and not _has_column(
        inspector, "order_items", "unit_cost"
    ):
        op.add_column(
            "order_items",
            sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("order_items") and _has_column(
        inspector, "order_items", "unit_cost"
    ):
        op.drop_column("order_items", "unit_cost")
