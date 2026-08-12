from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.core.money import money_to_float, to_decimal
from app.models.drawer import DrawerSession
from app.models.order import Order
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.user import User  # pyrefly: ignore [missing-import]
from app.schemas.drawer import DrawerSession as DrawerSessionSchema
from app.schemas.drawer import DrawerSessionClose, DrawerSessionCreate
from app.schemas.drawer import ShiftReconciliation as ShiftReconciliationSchema
from app.schemas.drawer import ShiftReconciliationCreate

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


@router.post("/reconcile/{session_id}", response_model=ShiftReconciliationSchema)
def reconcile_and_close_drawer(
    session_id: int,
    reconcile_in: ShiftReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
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
        .filter(ShiftReconciliation.drawer_session_id == drawer.id)
        .first()
    )
    if existing_reconciliation:
        raise HTTPException(
            status_code=400, detail="This drawer session has already been reconciled."
        )

    payment_base_query = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.drawer_session_id == drawer.id)
    )

    raw_cash_sales_total = payment_base_query.filter(
        func.lower(Payment.payment_method) == "cash"
    ).scalar()
    cash_sales_total = money_to_float(raw_cash_sales_total)

    raw_non_cash_sales_total = payment_base_query.filter(
        func.lower(Payment.payment_method) != "cash"
    ).scalar()
    non_cash_sales_total = money_to_float(raw_non_cash_sales_total)

    raw_refunds_total = (
        db.query(func.coalesce(func.sum(Refund.total_amount), 0.0))
        .join(Order, Refund.order_id == Order.id)
        .filter(Order.drawer_session_id == drawer.id)
        .scalar()
    )
    refunds_total = money_to_float(raw_refunds_total)

    raw_gross_sales_total = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(Order.drawer_session_id == drawer.id, Order.status == "completed")
        .scalar()
    )
    gross_sales_total = money_to_float(raw_gross_sales_total)

    raw_completed_order_count = (
        db.query(func.count(Order.id))
        .filter(Order.drawer_session_id == drawer.id, Order.status == "completed")
        .scalar()
    )
    completed_order_count = int(
        raw_completed_order_count if raw_completed_order_count is not None else 0
    )

    cash_pool = to_decimal(drawer.starting_cash) + to_decimal(cash_sales_total)
    expected_cash = money_to_float(cash_pool - to_decimal(refunds_total))
    expected_non_cash = non_cash_sales_total
    counted_non_cash = (
        money_to_float(reconcile_in.counted_non_cash)
        if reconcile_in.counted_non_cash is not None
        else expected_non_cash
    )

    reconciliation = ShiftReconciliation(
        drawer_session_id=drawer.id,
        closed_by_user_id=current_user.id,
        cash_sales_total=cash_sales_total,
        non_cash_sales_total=non_cash_sales_total,
        refunds_total=refunds_total,
        expected_cash=expected_cash,
        counted_cash=reconcile_in.counted_cash,
        cash_variance=reconcile_in.counted_cash - expected_cash,
        expected_non_cash=expected_non_cash,
        counted_non_cash=counted_non_cash,
        non_cash_variance=counted_non_cash - expected_non_cash,
        completed_order_count=completed_order_count,
        gross_sales_total=gross_sales_total,
        net_sales_total=gross_sales_total - refunds_total,
        notes=reconcile_in.notes,
    )
    db.add(reconciliation)

    drawer.ending_cash = reconcile_in.counted_cash
    drawer.expected_cash = expected_cash
    drawer.closed_at = datetime.now(timezone.utc)
    drawer.status = "closed"
    db.add(drawer)

    db.commit()
    db.refresh(reconciliation)
    return reconciliation


@router.get("/{session_id}/reconciliation", response_model=ShiftReconciliationSchema)
def get_drawer_reconciliation(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_active_user),
):
    drawer = db.query(DrawerSession).filter(DrawerSession.id == session_id).first()
    if not drawer:
        raise HTTPException(status_code=404, detail="Drawer session not found.")

    if not current_user.is_superuser and drawer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this drawer session."
        )

    reconciliation = (
        db.query(ShiftReconciliation)
        .filter(ShiftReconciliation.drawer_session_id == session_id)
        .first()
    )
    if not reconciliation:
        raise HTTPException(
            status_code=404, detail="No reconciliation found for this drawer session."
        )
    return reconciliation
