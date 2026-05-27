"""add_tax_engine_and_order_tax_lines

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-28 04:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("orders"):
        if not _has_column(inspector, "orders", "taxable_base_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "taxable_base_amount",
                    sa.Float(),
                    nullable=False,
                    server_default="0",
                ),
            )
        if not _has_column(inspector, "orders", "tax_total_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "tax_total_amount", sa.Float(), nullable=False, server_default="0"
                ),
            )
        if not _has_column(inspector, "orders", "grand_total_amount"):
            op.add_column(
                "orders",
                sa.Column(
                    "grand_total_amount",
                    sa.Float(),
                    nullable=False,
                    server_default="0",
                ),
            )

    if not inspector.has_table("tax_rules"):
        op.create_table(
            "tax_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("tax_scope", sa.String(), nullable=False, server_default="order"),
            sa.Column(
                "tax_mode",
                sa.String(),
                nullable=False,
                server_default="exclusive",
            ),
            sa.Column("rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("category_id", sa.Integer(), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_tax_rules_id"), "tax_rules", ["id"], unique=False)
        op.create_index(op.f("ix_tax_rules_name"), "tax_rules", ["name"], unique=False)
        op.create_index(
            op.f("ix_tax_rules_tax_scope"), "tax_rules", ["tax_scope"], unique=False
        )
        op.create_index(
            op.f("ix_tax_rules_tax_mode"), "tax_rules", ["tax_mode"], unique=False
        )
        op.create_index(
            op.f("ix_tax_rules_category_id"), "tax_rules", ["category_id"], unique=False
        )
        op.create_index(
            op.f("ix_tax_rules_product_id"), "tax_rules", ["product_id"], unique=False
        )
        op.create_index(
            op.f("ix_tax_rules_is_active"), "tax_rules", ["is_active"], unique=False
        )

    if not inspector.has_table("order_tax_lines"):
        op.create_table(
            "order_tax_lines",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("tax_rule_id", sa.Integer(), nullable=True),
            sa.Column("tax_name", sa.String(), nullable=False),
            sa.Column("tax_scope", sa.String(), nullable=False),
            sa.Column("tax_mode", sa.String(), nullable=False),
            sa.Column("tax_rate", sa.Float(), nullable=False),
            sa.Column("taxable_base", sa.Float(), nullable=False, server_default="0"),
            sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column(
                "applied_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
            ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["tax_rule_id"], ["tax_rules.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_order_tax_lines_id"),
            "order_tax_lines",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_order_tax_lines_order_id"),
            "order_tax_lines",
            ["order_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_order_tax_lines_tax_rule_id"),
            "order_tax_lines",
            ["tax_rule_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("order_tax_lines"):
        op.drop_index(
            op.f("ix_order_tax_lines_tax_rule_id"), table_name="order_tax_lines"
        )
        op.drop_index(op.f("ix_order_tax_lines_order_id"), table_name="order_tax_lines")
        op.drop_index(op.f("ix_order_tax_lines_id"), table_name="order_tax_lines")
        op.drop_table("order_tax_lines")

    if inspector.has_table("tax_rules"):
        op.drop_index(op.f("ix_tax_rules_is_active"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_product_id"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_category_id"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_tax_mode"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_tax_scope"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_name"), table_name="tax_rules")
        op.drop_index(op.f("ix_tax_rules_id"), table_name="tax_rules")
        op.drop_table("tax_rules")

    if inspector.has_table("orders"):
        if _has_column(inspector, "orders", "grand_total_amount"):
            op.drop_column("orders", "grand_total_amount")
        if _has_column(inspector, "orders", "tax_total_amount"):
            op.drop_column("orders", "tax_total_amount")
        if _has_column(inspector, "orders", "taxable_base_amount"):
            op.drop_column("orders", "taxable_base_amount")
