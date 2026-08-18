"""add_customers_and_loyalty

Revision ID: 9d4e2b1c7a8f
Revises: 8c7d9e1f2a3b
Create Date: 2026-05-28 00:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d4e2b1c7a8f"
down_revision: str | Sequence[str] | None = "8c7d9e1f2a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("customers"):
        op.create_table(
            "customers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("points_balance", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)
        op.create_index(op.f("ix_customers_name"), "customers", ["name"], unique=False)
        op.create_index(
            op.f("ix_customers_email"), "customers", ["email"], unique=False
        )
        op.create_index(
            op.f("ix_customers_phone"), "customers", ["phone"], unique=False
        )

    if not inspector.has_table("loyalty_transactions"):
        op.create_table(
            "loyalty_transactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=True),
            sa.Column("transaction_type", sa.String(), nullable=False),
            sa.Column("points_delta", sa.Integer(), nullable=False),
            sa.Column("balance_after", sa.Integer(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_loyalty_transactions_id"),
            "loyalty_transactions",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_loyalty_transactions_customer_id"),
            "loyalty_transactions",
            ["customer_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_loyalty_transactions_order_id"),
            "loyalty_transactions",
            ["order_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_loyalty_transactions_transaction_type"),
            "loyalty_transactions",
            ["transaction_type"],
            unique=False,
        )

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "customer_id" not in order_columns:
        op.add_column("orders", sa.Column("customer_id", sa.Integer(), nullable=True))

    if "redeemed_points" not in order_columns:
        op.add_column(
            "orders",
            sa.Column(
                "redeemed_points", sa.Integer(), nullable=False, server_default="0"
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "redeemed_points" in order_columns:
        op.drop_column("orders", "redeemed_points")
    if "customer_id" in order_columns:
        op.drop_column("orders", "customer_id")

    if inspector.has_table("loyalty_transactions"):
        op.drop_index(
            op.f("ix_loyalty_transactions_transaction_type"),
            table_name="loyalty_transactions",
        )
        op.drop_index(
            op.f("ix_loyalty_transactions_order_id"), table_name="loyalty_transactions"
        )
        op.drop_index(
            op.f("ix_loyalty_transactions_customer_id"),
            table_name="loyalty_transactions",
        )
        op.drop_index(
            op.f("ix_loyalty_transactions_id"), table_name="loyalty_transactions"
        )
        op.drop_table("loyalty_transactions")

    if inspector.has_table("customers"):
        op.drop_index(op.f("ix_customers_phone"), table_name="customers")
        op.drop_index(op.f("ix_customers_email"), table_name="customers")
        op.drop_index(op.f("ix_customers_name"), table_name="customers")
        op.drop_index(op.f("ix_customers_id"), table_name="customers")
        op.drop_table("customers")
