"""Shared pytest fixtures for FastAPI OctoPOS integration tests.

The test database is a dedicated PostgreSQL database (default
``octopos_test``, override with ``TEST_DATABASE_URL``). Schema is built by
running the real Alembic migration chain (``upgrade head``) ONCE per pytest
worker, then every test gets an empty-but-seeded schema via a fast
DELETE-based reset. The slowapi rate limiter is disabled so auth tests are
not throttled.

With pytest-xdist each worker runs against its own database
(``octopos_test`` / ``octopos_test_gw0`` / ``octopos_test_gw1`` / ...), so
parallel workers never collide.
"""

import hashlib
import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

DEFAULT_TEST_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/octopos_test"
_BASE_TEST_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_URL)

# Each xdist worker gets its own database (``octopos_test_gw0``, ...) so the
# schema build and per-test resets never contend across workers.
_worker = os.environ.get("PYTEST_XDIST_WORKER")
if _worker:
    TEST_DB_URL = (
        make_url(_BASE_TEST_URL)
        .set(database=f"{make_url(_BASE_TEST_URL).database}_{_worker}")
        .render_as_string(hide_password=False)
    )
else:
    TEST_DB_URL = _BASE_TEST_URL


def _ensure_database() -> None:
    """Create the per-worker test database if it does not exist yet."""
    url = make_url(TEST_DB_URL)
    admin_url = url.set(database="postgres").render_as_string(hide_password=False)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(
                    text(f'CREATE DATABASE "{url.database}" TEMPLATE template0')
                )
    finally:
        admin.dispose()


_ensure_database()

os.environ["ENVIRONMENT"] = "development"
os.environ["SQLALCHEMY_DATABASE_URI"] = TEST_DB_URL
# Keep product-image uploads out of the repo tree.
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="octopos-test-media-")

import _tenant_mode  # noqa: E402
import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.core.security as _security_mod  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.admin import views as _admin_mod  # noqa: E402
from app.api.endpoints import auth as _auth_mod  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402


def _fast_hash(password: str) -> str:
    return "test$" + hashlib.sha256(password.encode("utf-8")).hexdigest()


def _fast_verify(plain: str, hashed: str) -> bool:
    if hashed.startswith("test$"):
        return hashlib.sha256(plain.encode("utf-8")).hexdigest() == hashed[5:]
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# Replace bcrypt (~0.18s/hash) with a fast sha256 scheme. Done at conftest
# import time (not in a fixture) so it is in place before any test module
# does ``from app.core.security import verify_password``. Real bcrypt hashes
# still verify (the fake falls back), so pre-existing hashes keep working.
for _mod in (_security_mod, _auth_mod, _admin_mod):
    _mod.get_password_hash = _fast_hash
    _mod.verify_password = _fast_verify

ROOT = Path(__file__).resolve().parents[1]

test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

# Seed rows (RBAC roles/permissions, default tenant, default tax rule) are
# snapshotted after the one-time schema build and restored on every reset.
_SEED_TABLES: list[str] = []
_ALL_TABLES: list[str] | None = None
_SEQUENCES: list[str] | None = None
_SCHEMA_BUILT = False


def _all_tables() -> list[str]:
    global _ALL_TABLES
    if _ALL_TABLES is None:
        _ALL_TABLES = [
            t for t in inspect(test_engine).get_table_names() if t != "alembic_version"
        ]
    return _ALL_TABLES


def _sequences() -> list[str]:
    global _SEQUENCES
    if _SEQUENCES is None:
        with test_engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT sequence_name FROM information_schema.sequences "
                    "WHERE sequence_schema = 'public'"
                )
            ).fetchall()
        _SEQUENCES = [r[0] for r in rows]
    return _SEQUENCES


def _build_schema() -> None:
    """Build the schema once, then snapshot the migration seed rows.

    All objects are dropped first so the migrations always run their full
    chain (``upgrade head`` is a no-op on an already-current database) and
    no rows left over from a previous test run can contaminate the seed
    snapshot. Each table is dropped in its own committed transaction: one
    ``DROP SCHEMA ... CASCADE`` (or one transaction dropping everything)
    locks every object at once, which exceeds postgres'
    ``max_locks_per_transaction`` when several xdist workers build schemas
    simultaneously.
    """
    with test_engine.connect() as conn:
        for table in reversed(inspect(test_engine).get_table_names()):
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            conn.commit()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")

    with test_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS seed_backup"))
        for table in _all_tables():
            has_rows = conn.execute(text(f'SELECT 1 FROM "{table}" LIMIT 1')).scalar()
            if not has_rows:
                continue
            conn.execute(text(f'DROP TABLE IF EXISTS seed_backup."{table}"'))
            conn.execute(
                text(
                    f'CREATE TABLE seed_backup."{table}" AS SELECT * FROM public."{table}"'
                )
            )
            _SEED_TABLES.append(table)

    with test_engine.connect() as conn:
        role_names = {
            r[0] for r in conn.execute(text("SELECT name FROM roles")).fetchall()
        }
    missing = {"admin", "manager", "cashier"} - role_names
    assert not missing, f"RBAC seed missing after migration: {missing}"


class _AuthFactory:
    """Register/login helpers wired to a TestClient."""

    def __init__(self, client: TestClient):
        self._client = client

    def register(self, email: str, password: str = "TestPass123"):
        resp = self._client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def login(self, email: str, password: str = "TestPass123"):
        resp = self._client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": password},
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def user(self, email: str, password: str = "TestPass123"):
        """Register a user (gets the default cashier role) and return auth headers."""
        self.register(email, password)
        return self.login(email, password)


def _reset_database() -> None:
    """Clear all data and restore the migration seed rows.

    Uses DELETE (not TRUNCATE) inside a replica-role transaction: TRUNCATE
    forces a synchronous data-file sync on every table (~350ms each here),
    while DELETE on a mostly-empty schema is a few ms and resets sequences
    via setval. Replica role skips FK checks so delete order does not matter.
    """
    with test_engine.begin() as conn:
        dirty = [
            table
            for table in _all_tables()
            if conn.execute(text(f'SELECT 1 FROM "{table}" LIMIT 1')).scalar()
        ]

    with test_engine.begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        for table in dirty:
            conn.execute(text(f'DELETE FROM "{table}"'))
        for table in _SEED_TABLES:
            conn.execute(
                text(
                    f'INSERT INTO public."{table}" SELECT * FROM seed_backup."{table}"'
                )
            )
        for seq in _sequences():
            conn.execute(text(f"SELECT setval('\"{seq}\"', 1, false)"))
        for table in _SEED_TABLES:
            conn.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('public.\""
                    f"{table}\"', 'id'), COALESCE(MAX(id), 1), "
                    "COALESCE(MAX(id), 1) > 0) FROM public."
                    f'"{table}"'
                )
            )


@pytest.fixture(autouse=True)
def fresh_database(request):
    """Reset the database to a clean, seeded state before each test.

    The Alembic chain runs once per worker (``_build_schema``); every test
    then gets an empty schema with the migration seed rows restored. Tests
    marked ``no_db`` (pure unit tests) skip the reset entirely.
    """
    global _SCHEMA_BUILT
    if request.node.get_closest_marker("no_db"):
        yield
        return
    if not _SCHEMA_BUILT:
        _build_schema()
        _SCHEMA_BUILT = True
    _reset_database()
    yield


@pytest.fixture()
def client(monkeypatch):
    # Tests run single-tenant: force register/google-auth to reuse the
    # seeded "default" tenant (id 1) so users share one data world.
    from app.api.endpoints import auth as auth_endpoint
    from app.services.tenants import create_tenant as _create_tenant

    def _tenant_for_tests(db, name="Business"):
        if not _tenant_mode.FORCE_DEFAULT_TENANT:
            return _create_tenant(db, name)
        from app.models.tenant import Tenant

        tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
        if tenant is None:
            tenant = _create_tenant(db, name)
        return tenant

    monkeypatch.setattr(auth_endpoint, "create_tenant", _tenant_for_tests)

    from app.core.limiter import limiter
    from app.main import app

    limiter.enabled = False
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db():
    """Direct database session for seeding/asserting test data."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def auth_factory(client):
    return _AuthFactory(client)


@pytest.fixture()
def assign_role(db):
    def _assign(user_id: int, role_name: str):
        from app.models.rbac import Role
        from app.models.user import User

        user = db.get(User, user_id)
        role = db.query(Role).filter(Role.name == role_name).one()
        user.roles.append(role)
        db.commit()
        return user

    return _assign


@pytest.fixture()
def make_product(client):
    def _make(
        headers,
        name="Test Product",
        sku="SKU-TEST",
        price=100.0,
        stock=10,
        min_stock=0,
        max_stock=None,
        reorder_point=0,
        lead_time_days=0,
    ):
        cat_resp = client.post(
            "/api/v1/products/categories",
            headers=headers,
            json={"name": "General", "description": "Seed category"},
        )
        assert cat_resp.status_code == 200, cat_resp.text
        resp = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "name": name,
                "sku": sku,
                "price": price,
                "stock_quantity": stock,
                "min_stock": min_stock,
                "max_stock": max_stock,
                "reorder_point": reorder_point,
                "lead_time_days": lead_time_days,
                "category_id": cat_resp.json()["id"],
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    return _make


@pytest.fixture()
def open_drawer(client):
    def _open(headers, starting_cash=100.0):
        resp = client.post(
            "/api/v1/drawers/open",
            headers=headers,
            json={"starting_cash": starting_cash},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    return _open


@pytest.fixture()
def manager_headers(client, auth_factory, assign_role):
    """A user promoted to the seeded manager role (has products:manage)."""
    user = auth_factory.register("manager@example.com")
    assign_role(user["id"], "manager")
    return auth_factory.login("manager@example.com")


@pytest.fixture()
def admin_headers(client, auth_factory, assign_role):
    """A user promoted to the seeded admin role (has purchasing:approve)."""
    user = auth_factory.register("admin@example.com")
    assign_role(user["id"], "admin")
    return auth_factory.login("admin@example.com")


@pytest.fixture()
def cashier_headers(auth_factory):
    """Default cashier user (no products/manage permission)."""
    return auth_factory.user("cashier@example.com")


def order_payload(product_id, quantity=1, idempotency_key=None, customer_id=None):
    payload = {"items": [{"product_id": product_id, "quantity": quantity}]}
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    if customer_id is not None:
        payload["customer_id"] = customer_id
    return payload
