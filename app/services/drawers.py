from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.money import money_to_float, to_decimal
from app.models.drawer import DrawerSession
from app.models.order import Order
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.shift_reconciliation import ShiftReconciliation
from app.schemas.drawer import ShiftReconciliationCreate


def compute_drawer_totals(db: Session, drawer: DrawerSession) -> dict[str, float]:
    """Aggregate sales, refund, and order totals for a drawer session."""
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

    refund_base_query = (
        db.query(func.coalesce(func.sum(Refund.total_amount), 0.0))
        .join(Order, Refund.order_id == Order.id)
        .filter(Order.drawer_session_id == drawer.id)
    )
    # Legacy refunds with no payment method recorded count as cash refunds.
    cash_refund_filter = (
        func.lower(func.coalesce(Refund.payment_method, "cash")) == "cash"
    )

    raw_cash_refunds_total = refund_base_query.filter(cash_refund_filter).scalar()
    cash_refunds_total = money_to_float(raw_cash_refunds_total)

    raw_non_cash_refunds_total = refund_base_query.filter(~cash_refund_filter).scalar()
    non_cash_refunds_total = money_to_float(raw_non_cash_refunds_total)

    raw_refunds_total = refund_base_query.scalar()
    refunds_total = money_to_float(raw_refunds_total)

    raw_gross_sales_total = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(
            Order.drawer_session_id == drawer.id,
            Order.status.in_(["serving", "completed"]),
        )
        .scalar()
    )
    gross_sales_total = money_to_float(raw_gross_sales_total)

    raw_completed_order_count = (
        db.query(func.count(Order.id))
        .filter(
            Order.drawer_session_id == drawer.id,
            Order.status.in_(["serving", "completed"]),
        )
        .scalar()
    )
    completed_order_count = int(
        raw_completed_order_count if raw_completed_order_count is not None else 0
    )

    return {
        "cash_sales_total": cash_sales_total,
        "non_cash_sales_total": non_cash_sales_total,
        "refunds_total": refunds_total,
        "cash_refunds_total": cash_refunds_total,
        "non_cash_refunds_total": non_cash_refunds_total,
        "gross_sales_total": gross_sales_total,
        "completed_order_count": completed_order_count,
    }


def build_reconciliation(
    db: Session,
    drawer: DrawerSession,
    closed_by_user_id: int,
    reconcile_in: ShiftReconciliationCreate,
) -> ShiftReconciliation:
    """Compute expected totals and variances for a drawer reconciliation."""
    totals = compute_drawer_totals(db, drawer)

    cash_pool = to_decimal(drawer.starting_cash) + to_decimal(
        totals["cash_sales_total"]
    )
    expected_cash = money_to_float(cash_pool - to_decimal(totals["cash_refunds_total"]))
    expected_non_cash = money_to_float(
        to_decimal(totals["non_cash_sales_total"])
        - to_decimal(totals["non_cash_refunds_total"])  # noqa: W503
    )
    counted_non_cash = (
        money_to_float(reconcile_in.counted_non_cash)
        if reconcile_in.counted_non_cash is not None
        else expected_non_cash
    )

    return ShiftReconciliation(
        drawer_session_id=drawer.id,
        tenant_id=drawer.tenant_id,
        closed_by_user_id=closed_by_user_id,
        cash_sales_total=totals["cash_sales_total"],
        non_cash_sales_total=totals["non_cash_sales_total"],
        refunds_total=totals["refunds_total"],
        cash_refunds_total=totals["cash_refunds_total"],
        non_cash_refunds_total=totals["non_cash_refunds_total"],
        expected_cash=expected_cash,
        counted_cash=reconcile_in.counted_cash,
        cash_variance=reconcile_in.counted_cash - expected_cash,
        expected_non_cash=expected_non_cash,
        counted_non_cash=counted_non_cash,
        non_cash_variance=counted_non_cash - expected_non_cash,
        completed_order_count=totals["completed_order_count"],
        gross_sales_total=totals["gross_sales_total"],
        net_sales_total=money_to_float(
            to_decimal(totals["gross_sales_total"])
            - to_decimal(totals["refunds_total"])  # noqa: W503
        ),
        notes=reconcile_in.notes,
    )
