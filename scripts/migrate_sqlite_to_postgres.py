"""One-time data migration: copy all rows from a SQLite database into
PostgreSQL.

The target PostgreSQL schema is built from the real Alembic migration chain
(``upgrade head``) before copying, so seed data created by migrations
(roles/permissions/role_permissions from 0001, the default tax rule from
0004) already exists in the target. Those tables are copied with
``ON CONFLICT DO NOTHING`` so migration seeds win and only user-added rows
are inserted.

Usage::

    python scripts/migrate_sqlite_to_postgres.py \
        --sqlite ./sql_app.db \
        --postgres "postgresql+psycopg://postgres:postgres@localhost:5432/octopos"

Defaults: ``--sqlite ./sql_app.db``,
``--postgres`` from the ``SQLALCHEMY_DATABASE_URI`` env var (or the
docker-compose default URI).
"""

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from alembic import command
from alembic.config import Config

# Tables fully seeded by migrations. Copy user-added rows, but never
# overwrite the migration seed rows (they share the same PKs).
SEEDED_TABLES = {"roles", "permissions", "role_permissions", "tax_rules"}

DEFAULT_POSTGRES_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/octopos"


def build_pg_schema(pg_url: str, alembic_ini: Path) -> None:
    """Run the Alembic migration chain against the target database.

    ``alembic/env.py`` resolves the URL from the app settings singleton
    (``app.core.config.settings``), so the env var must be set before the
    Config import chain reads it.
    """
    os.environ["SQLALCHEMY_DATABASE_URI"] = pg_url
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", pg_url)
    command.upgrade(cfg, "head")


def topological_order(engine, tables: list[str]) -> list[str]:
    """Order tables so parents come before children (FK dependency sort)."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    deps: dict[str, set[str]] = {t: set() for t in tables}
    for t in tables:
        for fk in inspector.get_foreign_keys(t):
            referred = fk["referred_table"]
            if referred in tables and referred != t:
                deps[t].add(referred)

    ordered: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        for dep in deps[name]:
            visit(dep)
        ordered.append(name)

    for t in tables:
        visit(t)
    return ordered


def sync_sequences(pg_conn: Connection) -> None:
    """Advance every PostgreSQL sequence past the current max value.

    SQLite has no sequences; after copying rows the SERIAL/identity columns
    still start at 1 and would collide with copied primary keys on the next
    insert.
    """
    rows = pg_conn.execute(
        text(
            "SELECT pg_get_serial_sequence(t.table_name, c.column_name) AS seq, t.table_name, c.column_name "
            "FROM information_schema.tables t "
            "JOIN information_schema.columns c USING (table_schema, table_name) "
            "WHERE t.table_schema = 'public' AND c.column_default LIKE 'nextval(%'"
        )
    ).all()
    for seq, table, column in rows:
        pg_conn.execute(
            text(f"SELECT setval('{seq}', COALESCE(MAX({column}), 1)) FROM {table}")
        )
    if rows:
        print(f"  sequences synced: {len(rows)}")


def copy_table(
    sqlite_conn: Connection,
    pg_conn: Connection,
    sqlite_md: MetaData,
    pg_md: MetaData,
    table_name: str,
) -> int:
    sqlite_tbl = Table(table_name, sqlite_md, autoload_with=sqlite_conn.engine)
    pg_tbl = Table(table_name, pg_md, autoload_with=pg_conn.engine)

    # Copy only columns present in both schemas (SQLite DBs predating later
    # migrations are missing columns).
    cols = [c.name for c in sqlite_tbl.columns if c.name in pg_tbl.c]
    if not cols:
        print(f"  {table_name}: no shared columns, skipping")
        return 0

    rows = [
        dict(r)
        for r in sqlite_conn.execute(
            select(*[sqlite_tbl.c[c] for c in cols])
        ).mappings()
    ]
    if not rows:
        print(f"  {table_name}: 0 rows")
        return 0

    # Multi-tenant era: tenant-scoped columns that legacy SQLite schemas
    # predate are assigned to the seeded default tenant (id 1). Superusers
    # keep tenant_id NULL, mirroring migration 0011's backfill semantics.
    if "tenant_id" in pg_tbl.c and "tenant_id" not in cols:
        for row in rows:
            row["tenant_id"] = 1 if not row.get("is_superuser") else None

    stmt = pg_insert(pg_tbl)
    if table_name in SEEDED_TABLES:
        stmt = stmt.on_conflict_do_nothing()
    pg_conn.execute(stmt, rows)
    print(f"  {table_name}: {len(rows)} rows")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite", default="./sql_app.db", help="Path to SQLite database"
    )
    parser.add_argument(
        "--postgres",
        default=None,
        help="PostgreSQL URL (default: SQLALCHEMY_DATABASE_URI or docker-compose URL)",
    )
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        print(f"SQLite database not found: {sqlite_path}", file=sys.stderr)
        return 1

    import os

    pg_url = (
        args.postgres or os.getenv("SQLALCHEMY_DATABASE_URI") or DEFAULT_POSTGRES_URL
    )
    if not pg_url.startswith("postgresql"):
        print(f"Expected a postgresql:// URL, got: {pg_url}", file=sys.stderr)
        return 1

    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"

    print(f"SQLite:   {sqlite_path}")
    print(f"Postgres: {pg_url}")
    print("Building PostgreSQL schema (alembic upgrade head) ...")
    build_pg_schema(pg_url, alembic_ini)
    print("Schema ready.")

    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    pg_engine = create_engine(pg_url)

    from sqlalchemy import inspect

    sqlite_inspector = inspect(sqlite_engine)
    tables = [t for t in sqlite_inspector.get_table_names() if t != "alembic_version"]
    order = topological_order(sqlite_engine, tables)

    sqlite_md = MetaData()
    pg_md = MetaData()
    total = 0
    with sqlite_engine.connect() as sqlite_conn, pg_engine.connect() as pg_conn:
        # Interpret naive datetimes written by the SQLite era as UTC.
        with pg_conn.begin():
            pg_conn.execute(text("SET TIME ZONE 'UTC'"))
            for table in order:
                total += copy_table(sqlite_conn, pg_conn, sqlite_md, pg_md, table)
            sync_sequences(pg_conn)
    print(f"Done: {total} rows copied across {len(order)} tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
