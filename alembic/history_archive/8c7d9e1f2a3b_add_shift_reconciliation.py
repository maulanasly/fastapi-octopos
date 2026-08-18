"""add_shift_reconciliation

Revision ID: 8c7d9e1f2a3b
Revises: 7a1d2c3e4f5b
Create Date: 2026-05-28 00:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c7d9e1f2a3b"
down_revision: str | Sequence[str] | None = "7a1d2c3e4f5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("shift_reconciliations"):
        op.create_table(
            "shift_reconciliations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drawer_session_id", sa.Integer(), nullable=False),
            sa.Column("closed_by_user_id", sa.Integer(), nullable=False),
            sa.Column("cash_sales_total", sa.Float(), nullable=False),
            sa.Column("non_cash_sales_total", sa.Float(), nullable=False),
            sa.Column("refunds_total", sa.Float(), nullable=False),
            sa.Column("expected_cash", sa.Float(), nullable=False),
            sa.Column("counted_cash", sa.Float(), nullable=False),
            sa.Column("cash_variance", sa.Float(), nullable=False),
            sa.Column("expected_non_cash", sa.Float(), nullable=False),
            sa.Column("counted_non_cash", sa.Float(), nullable=False),
            sa.Column("non_cash_variance", sa.Float(), nullable=False),
            sa.Column("completed_order_count", sa.Integer(), nullable=False),
            sa.Column("gross_sales_total", sa.Float(), nullable=False),
            sa.Column("net_sales_total", sa.Float(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["drawer_session_id"], ["drawer_sessions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_shift_reconciliations_id"),
            "shift_reconciliations",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_shift_reconciliations_closed_by_user_id"),
            "shift_reconciliations",
            ["closed_by_user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_shift_reconciliations_drawer_session_id"),
            "shift_reconciliations",
            ["drawer_session_id"],
            unique=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("shift_reconciliations"):
        op.drop_index(
            op.f("ix_shift_reconciliations_drawer_session_id"),
            table_name="shift_reconciliations",
        )
        op.drop_index(
            op.f("ix_shift_reconciliations_closed_by_user_id"),
            table_name="shift_reconciliations",
        )
        op.drop_index(
            op.f("ix_shift_reconciliations_id"), table_name="shift_reconciliations"
        )
        op.drop_table("shift_reconciliations")
