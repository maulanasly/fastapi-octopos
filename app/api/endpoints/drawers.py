from datetime import UTC, datetime

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.audit import log_action
from app.core.database import get_db
from app.models.drawer import DrawerSession
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.user import User  # pyrefly: ignore [missing-import]
from app.schemas.drawer import DrawerSession as DrawerSessionSchema
from app.schemas.drawer import (
    DrawerSessionClose,
    DrawerSessionCreate,
    ShiftReconciliationCreate,
)
from app.schemas.drawer import ShiftReconciliation as ShiftReconciliationSchema
from app.services.drawers import build_reconciliation

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
            DrawerSession.user_id == current_user.id,
            DrawerSession.status == "open",
            DrawerSession.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="An active drawer session already exists."
        )
    drawer = DrawerSession(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        starting_cash=drawer_in.starting_cash,
        expected_cash=drawer_in.expected_cash or 0.0,
        status="open",
        opened_at=datetime.now(UTC),
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
            DrawerSession.user_id == current_user.id,
            DrawerSession.status == "open",
            DrawerSession.tenant_id == current_user.tenant_id,
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
            DrawerSession.tenant_id == current_user.tenant_id,
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
    drawer.closed_at = datetime.now(UTC)
    drawer.status = "closed"
    db.add(drawer)
    db.commit()
    db.refresh(drawer)
    return drawer


@router.post("/reconcile/{session_id}", response_model=ShiftReconciliationSchema)
def reconcile_and_close_drawer(
    session_id: int,
    reconcile_in: ShiftReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        drawer = (
            db.query(DrawerSession)
            .filter(
                DrawerSession.id == session_id,
                DrawerSession.tenant_id == current_user.tenant_id,
            )
            .first()
        )
    else:
        drawer = db.query(DrawerSession).filter(DrawerSession.id == session_id).first()
    if not drawer:
        raise HTTPException(status_code=404, detail="Drawer session not found.")

    if not current_user.is_superuser and drawer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to reconcile this drawer session."
        )

    if drawer.status != "open":
        raise HTTPException(
            status_code=400, detail="Only open drawer sessions can be reconciled."
        )

    existing_reconciliation = (
        db.query(ShiftReconciliation)
        .filter(
            ShiftReconciliation.drawer_session_id == drawer.id,
            ShiftReconciliation.tenant_id == drawer.tenant_id,
        )
        .first()
    )
    if existing_reconciliation:
        raise HTTPException(
            status_code=400, detail="This drawer session has already been reconciled."
        )

    reconciliation = build_reconciliation(
        db=db,
        drawer=drawer,
        closed_by_user_id=current_user.id,
        reconcile_in=reconcile_in,
    )
    db.add(reconciliation)

    drawer.ending_cash = reconcile_in.counted_cash
    drawer.expected_cash = reconciliation.expected_cash
    drawer.closed_at = datetime.now(UTC)
    drawer.status = "closed"
    db.add(drawer)

    log_action(
        db=db,
        action="drawer.reconcile",
        user_id=current_user.id,
        resource_type="drawer_session",
        resource_id=drawer.id,
        details={
            "expected_cash": str(reconciliation.expected_cash),
            "counted_cash": str(reconcile_in.counted_cash),
        },
    )
    db.commit()
    db.refresh(reconciliation)
    return reconciliation


@router.get("/{session_id}/reconciliation", response_model=ShiftReconciliationSchema)
def get_drawer_reconciliation(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        drawer = (
            db.query(DrawerSession)
            .filter(
                DrawerSession.id == session_id,
                DrawerSession.tenant_id == current_user.tenant_id,
            )
            .first()
        )
    else:
        drawer = db.query(DrawerSession).filter(DrawerSession.id == session_id).first()
    if not drawer:
        raise HTTPException(status_code=404, detail="Drawer session not found.")

    if not current_user.is_superuser and drawer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this drawer session."
        )

    reconciliation = (
        db.query(ShiftReconciliation)
        .filter(
            ShiftReconciliation.drawer_session_id == session_id,
            ShiftReconciliation.tenant_id == drawer.tenant_id,
        )
        .first()
    )
    if not reconciliation:
        raise HTTPException(
            status_code=404, detail="No reconciliation found for this drawer session."
        )
    return reconciliation
