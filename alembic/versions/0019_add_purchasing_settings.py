"""add_purchasing_settings

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "purchasing_settings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "auto_po_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "auto_po_lookback_days", sa.Integer(), nullable=False, server_default="30"
        ),
        sa.Column(
            "auto_po_min_stock_trigger",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.UniqueConstraint("tenant_id", name="uq_purchasing_settings_tenant_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("purchasing_settings")
