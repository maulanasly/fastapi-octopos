"""relax_audit_logs_tenant_id

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-17 13:00:00.000000

Platform-level actions (superuser admin panel, tenant_id NULL users) may
not belong to any tenant; relax audit_logs.tenant_id to NULL so those
entries can be recorded without inventing a tenant.

Portable across PostgreSQL (direct ALTER) and SQLite (batch rebuild).
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("audit_logs") as batch_op:
            batch_op.alter_column("tenant_id", nullable=True)
    else:
        op.alter_column("audit_logs", "tenant_id", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("audit_logs") as batch_op:
            batch_op.alter_column("tenant_id", nullable=False)
    else:
        op.alter_column("audit_logs", "tenant_id", nullable=False)
