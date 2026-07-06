"""Pytest configuration and fixtures for FastAPI OctoPOS tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URI = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URI, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def override_get_db(db):
    """Override get_db dependency to use test database."""
    from app.core.database import get_db

    def _override():
        try:
            yield db
        finally:
            pass

    return _override
