"""seed_default_tax_rule

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-16 09:00:00.000000

Seeds a configurable default tax rule so new installs do not silently
sell without tax. Rate comes from the DEFAULT_TAX_RATE env var (0 keeps
a jurisdiction-neutral default). Idempotent: skips when any order-scope
tax rule already exists.
"""
import os
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("tax_rules"):
        return

    existing = bind.execute(sa.text("SELECT COUNT(*) FROM tax_rules")).scalar()
    if existing:
        return

    rate = float(os.getenv("DEFAULT_TAX_RATE", "0.0"))
    name = os.getenv("DEFAULT_TAX_NAME", "VAT")
    bind.execute(
        sa.text(
            "INSERT INTO tax_rules (name, description, tax_scope, tax_mode, rate, "
            "starts_at, ends_at, is_active, created_at, updated_at) "
            "VALUES (:name, :desc, 'order', 'exclusive', :rate, NULL, NULL, 1, "
            "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {
            "name": name,
            "desc": f"Default {name} seeded by migration (rate {rate:.4f})",
            "rate": rate,
        },
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("tax_rules"):
        return

    bind.execute(
        sa.text("DELETE FROM tax_rules WHERE description LIKE 'Default % seeded%'")
    )
