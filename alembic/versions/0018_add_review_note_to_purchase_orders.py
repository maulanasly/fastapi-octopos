"""add review note to purchase orders

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-19 13:05:00.000000

Adds ``review_note`` to ``purchase_orders`` for the review workflow
(``draft -> pending_review -> ordered | rejected``).

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "purchase_orders",
        sa.Column("review_note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("purchase_orders", "review_note")
