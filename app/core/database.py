from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Shared-cache in-memory SQLite (tests) must keep a single persistent
# connection per engine: sqladmin runs sync DB work in anyio worker
# threads, and per-thread connection churn on a memory DB closes/rebuilds
# it under concurrent sessions. StaticPool fixes that.
_pool_kwargs = (
    {"poolclass": StaticPool}
    if "mode=memory" in settings.SQLALCHEMY_DATABASE_URI
    else {}
)

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    **_pool_kwargs,
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
