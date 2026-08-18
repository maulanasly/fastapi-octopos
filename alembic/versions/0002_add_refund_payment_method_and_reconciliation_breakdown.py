"""add_refund_payment_method_and_reconciliation_breakdown

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-12 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("refunds") and not _has_column(
        inspector, "refunds", "payment_method"
    ):
        op.add_column(
            "refunds",
            sa.Column("payment_method", sa.String(), nullable=True),
        )

    if inspector.has_table("shift_reconciliations"):
        if not _has_column(inspector, "shift_reconciliations", "cash_refunds_total"):
            op.add_column(
                "shift_reconciliations",
                sa.Column(
                    "cash_refunds_total",
                    sa.Numeric(12, 2),
                    nullable=False,
                    server_default="0",
                ),
            )
        if not _has_column(
            inspector, "shift_reconciliations", "non_cash_refunds_total"
        ):
            op.add_column(
                "shift_reconciliations",
                sa.Column(
                    "non_cash_refunds_total",
                    sa.Numeric(12, 2),
                    nullable=False,
                    server_default="0",
                ),
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("refunds") and _has_column(
        inspector, "refunds", "payment_method"
    ):
        op.drop_column("refunds", "payment_method")

    if inspector.has_table("shift_reconciliations"):
        if _has_column(inspector, "shift_reconciliations", "cash_refunds_total"):
            op.drop_column("shift_reconciliations", "cash_refunds_total")
        if _has_column(inspector, "shift_reconciliations", "non_cash_refunds_total"):
            op.drop_column("shift_reconciliations", "non_cash_refunds_total")
