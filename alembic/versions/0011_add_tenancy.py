"""add_tenancy

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-17 12:00:00.000000

Introduces multi-tenancy (shared schema, one ``tenant_id`` column per
tenant-scoped table):

- new ``tenants`` table, seeded with tenant 1 ("Default Business")
- every tenant-scoped table gains ``tenant_id`` (NOT NULL except
  ``users``, where NULL marks a platform superuser) and all existing rows
  are backfilled to tenant 1
- global uniques on products.sku, promotions.code and users.email are
  replaced by per-tenant composite uniques, so the same SKU/code/email can
  exist in different tenants

Portable across PostgreSQL and SQLite (batch mode for the SQLite rebuilds
required by column/constraint changes).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES: list[str] = [
    "users",
    "categories",
    "products",
    "customers",
    "loyalty_transactions",
    "promotions",
    "tax_rules",
    "order_tax_lines",
    "orders",
    "order_items",
    "payments",
    "refunds",
    "refund_items",
    "drawer_sessions",
    "shift_reconciliations",
    "stock_movements",
    "suppliers",
    "purchase_orders",
    "purchase_order_items",
    "purchase_invoices",
    "purchase_invoice_items",
    "sync_event_logs",
    "audit_logs",
    "localization_settings",
    "refresh_tokens",
]


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _add_column(table: str, column: sa.Column) -> None:
    if _is_sqlite():
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(column)
    else:
        op.add_column(table, column)


def _set_not_null(table: str, column: str) -> None:
    if _is_sqlite():
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(column, nullable=False)
    else:
        op.alter_column(table, column, nullable=False)


def _create_unique(table: str, name: str, columns: list[str]) -> None:
    if _is_sqlite():
        with op.batch_alter_table(table) as batch_op:
            batch_op.create_unique_constraint(name, columns)
    else:
        op.create_unique_constraint(name, table, columns)


def _drop_index(name: str, table: str) -> None:
    if _is_sqlite():
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_index(name)
    else:
        op.drop_index(name, table_name=table)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- tenants ---------------------------------------------------------
    if not inspector.has_table("tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_tenants_id", "tenants", ["id"])
        op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
        op.bulk_insert(
            sa.table(
                "tenants",
                sa.column("id", sa.Integer),
                sa.column("name", sa.String),
                sa.column("slug", sa.String),
            ),
            [{"id": 1, "name": "Default Business", "slug": "default"}],
        )
        if bind.dialect.name == "postgresql":
            op.execute(
                "SELECT setval(pg_get_serial_sequence('tenants', 'id'), "
                "(SELECT MAX(id) FROM tenants))"
            )

    # --- tenant_id on every tenant-scoped table --------------------------
    for table in TENANT_TABLES:
        if not inspector.has_table(table):
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if "tenant_id" in columns:
            continue

        _add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.Integer(),
                sa.ForeignKey("tenants.id", name=f"fk_{table}_tenant_id"),
                nullable=True,
            ),
        )
        if table == "users":
            op.execute("UPDATE users SET tenant_id = 1 WHERE is_superuser = false")
        else:
            op.execute(f"UPDATE {table} SET tenant_id = 1")
        if table != "users":
            _set_not_null(table, "tenant_id")
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])

    # --- per-tenant uniques ----------------------------------------------
    _drop_index("ix_products_sku", "products")
    _drop_index("ix_promotions_code", "promotions")
    _drop_index("ix_users_email", "users")
    _create_unique("products", "uq_products_tenant_sku", ["tenant_id", "sku"])
    _create_unique("promotions", "uq_promotions_tenant_code", ["tenant_id", "code"])
    _create_unique("users", "uq_users_tenant_email", ["tenant_id", "email"])


def _drop_unique(table: str, name: str) -> None:
    if _is_sqlite():
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(name, type_="unique")
    else:
        op.drop_constraint(name, table, type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    _drop_unique("products", "uq_products_tenant_sku")
    _drop_unique("promotions", "uq_promotions_tenant_code")
    _drop_unique("users", "uq_users_tenant_email")
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_promotions_code", "promotions", ["code"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in reversed(TENANT_TABLES):
        if not inspector.has_table(table):
            continue
        index_name = f"ix_{table}_tenant_id"
        if any(i["name"] == index_name for i in inspector.get_indexes(table)):
            # SQLite batch recreate replays the table's indexes onto the
            # rebuilt table, so the tenant_id index must go first.
            if _is_sqlite():
                with op.batch_alter_table(table) as batch_op:
                    batch_op.drop_index(index_name)
            else:
                op.drop_index(index_name, table_name=table)
        if _is_sqlite():
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_column("tenant_id")
        else:
            op.drop_column(table, "tenant_id")

    op.drop_table("tenants")
