"""Run background tasks exactly once per cluster using a PostgreSQL
advisory lock.

Each uvicorn worker starts its own copy of the reservation-sweep and
auto-purchase-order loops (see ``app.main.lifespan``). Without a guard the
work would be duplicated per worker. A session-level ``pg_try_advisory_lock``
on a dedicated connection makes the task a single-writer operation; workers
that fail to acquire the lock simply skip this run. On SQLite (single
process dev mode) the task always runs.
"""
from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Arbitrary stable identifiers (must fit PostgreSQL bigint).
RESERVATION_SWEEP_LOCK = 8432630001
AUTO_PO_LOCK = 8432630002


def run_exclusive(engine: Engine, lock_key: int, task: Callable[[], None]) -> bool:
    """Run ``task`` under a named advisory lock.

    Returns True when the task ran, False when another worker held the lock.
    """
    if engine.dialect.name != "postgresql":
        task()
        return True

    conn = engine.connect()
    try:
        acquired = conn.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": lock_key}
        ).scalar()
        if not acquired:
            return False
        try:
            task()
            return True
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock_key})
    finally:
        conn.close()
