"""add supplier payments

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-19 12:39:48.652431

Adds ``supplier_payments``: recording payments against approved purchase
invoices, with the same review workflow as invoices
(``draft -> pending_review -> approved | rejected``). Approval is the
paid recognition point; partial payments are allowed and overpayment is
rejected by the service layer.

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "supplier_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["purchase_invoices.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_supplier_payments_tenant_id", "supplier_payments", ["tenant_id"]
    )
    op.create_index(
        "ix_supplier_payments_supplier_id", "supplier_payments", ["supplier_id"]
    )
    op.create_index(
        "ix_supplier_payments_invoice_id", "supplier_payments", ["invoice_id"]
    )
    op.create_index("ix_supplier_payments_user_id", "supplier_payments", ["user_id"])
    op.create_index("ix_supplier_payments_status", "supplier_payments", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_supplier_payments_status", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_user_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_invoice_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_supplier_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_tenant_id", table_name="supplier_payments")
    op.drop_table("supplier_payments")
