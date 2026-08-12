"""Shared pytest fixtures for FastAPI OctoPOS integration tests.

The test database is an in-memory SQLite DB shared between the app engine and
Alembic via a ``file::memory:`` URI with shared cache. Schema is built by
running the real Alembic migration chain (``upgrade head``) on every test so
tests exercise the exact production schema, including the RBAC seed data.
The slowapi rate limiter is disabled so auth tests are not throttled.
"""
import os
from pathlib import Path

os.environ["ENVIRONMENT"] = "development"
os.environ[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///file:octopos_test?mode=memory&cache=shared&uri=true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.core.database import Base, SessionLocal  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEST_DB_URL = os.environ["SQLALCHEMY_DATABASE_URI"]

# One persistent connection for the whole session: with StaticPool the
# engine's connection is never re-created, so the shared in-memory DB
# survives worker-thread session churn from sqladmin.
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


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


@pytest.fixture(scope="session")
def keep_db_connection():
    """Holds the shared-cache in-memory SQLite DB alive for the session."""
    conn = test_engine.connect()
    yield
    conn.close()


@pytest.fixture(autouse=True)
def fresh_database(keep_db_connection):
    """Rebuild schema from the real Alembic migration chain before each test."""
    Base.metadata.drop_all(bind=test_engine)
    with test_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")
    yield


@pytest.fixture()
def client():
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
def cashier_headers(auth_factory):
    """Default cashier user (no products/manage permission)."""
    return auth_factory.user("cashier@example.com")


def order_payload(product_id, quantity=1, idempotency_key=None):
    payload = {"items": [{"product_id": product_id, "quantity": quantity}]}
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    return payload
