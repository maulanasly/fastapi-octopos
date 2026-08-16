"""Health and readiness endpoints for deployment probes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("/health", tags=["health"])
def health():
    """Liveness probe - the process is up and serving requests."""
    return {"status": "ok"}


@router.get("/health/ready", tags=["health"])
def readiness(db: Session = Depends(get_db)):
    """Readiness probe - verifies the database is reachable."""
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
