from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# SQLite-only behaviors:
# - Shared-cache in-memory SQLite (tests) must keep a single persistent
#   connection per engine: sqladmin runs sync DB work in anyio worker
#   threads, and per-thread connection churn on a memory DB closes/rebuilds
#   it under concurrent sessions. StaticPool fixes that.
# - check_same_thread is a sqlite3-only kwarg; psycopg rejects it.
is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite")

_pool_kwargs = (
    {"poolclass": StaticPool}
    if "mode=memory" in settings.SQLALCHEMY_DATABASE_URI
    else {}
)
_connect_args = {"check_same_thread": False} if is_sqlite else {}
_engine_kwargs = {
    # Dead-connection recovery for Postgres behind load balancers/proxies.
    "pool_pre_ping": True,
}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args=_connect_args,
    **_pool_kwargs,
    **_engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
