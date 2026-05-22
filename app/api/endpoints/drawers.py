from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.drawer import DrawerSession
from app.models.user import User  # pyrefly: ignore [missing-import]
from app.schemas.drawer import DrawerSession as DrawerSessionSchema
from app.schemas.drawer import DrawerSessionClose, DrawerSessionCreate

router = APIRouter()


@router.post("/open", response_model=DrawerSessionSchema)
def open_drawer(
    drawer_in: DrawerSessionCreate,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    # Ensure no other open drawer for this user
    existing = (
        db.query(DrawerSession)
        .filter(
            DrawerSession.user_id == current_user.id, DrawerSession.status == "open"
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="An active drawer session already exists."
        )
    drawer = DrawerSession(
        user_id=current_user.id,
        starting_cash=drawer_in.starting_cash,
        expected_cash=drawer_in.expected_cash or 0.0,
        status="open",
        opened_at=datetime.now(timezone.utc),
    )
    db.add(drawer)
    db.commit()
    db.refresh(drawer)
    return drawer


@router.get("/active", response_model=DrawerSessionSchema)
def get_active_drawer(
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    drawer = (
        db.query(DrawerSession)
        .filter(
            DrawerSession.user_id == current_user.id, DrawerSession.status == "open"
        )
        .first()
    )
    if not drawer:
        raise HTTPException(status_code=404, detail="No active drawer session found.")
    return drawer


@router.post("/close/{session_id}", response_model=DrawerSessionSchema)
def close_drawer(
    session_id: int,
    close_in: DrawerSessionClose,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    drawer = (
        db.query(DrawerSession)
        .filter(
            DrawerSession.id == session_id,
            DrawerSession.user_id == current_user.id,
            DrawerSession.status == "open",
        )
        .first()
    )
    if not drawer:
        raise HTTPException(status_code=404, detail="Active drawer session not found.")
    drawer.ending_cash = close_in.ending_cash
    drawer.expected_cash = (
        close_in.expected_cash
        if close_in.expected_cash is not None
        else drawer.expected_cash
    )
    drawer.closed_at = datetime.now(timezone.utc)
    drawer.status = "closed"
    db.add(drawer)
    db.commit()
    db.refresh(drawer)
    return drawer
