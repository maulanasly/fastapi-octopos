from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Category, Product
from app.models.purchase import PurchaseInvoice, PurchaseOrder, PurchaseOrderItem
from app.models.refund import Refund
from app.models.shift_reconciliation import ShiftReconciliation


def get_shift_report_data(db: Session, reconciliation_id: int) -> dict:
    """Full shift report for one drawer reconciliation."""
    reconciliation = (
        db.query(ShiftReconciliation)
        .filter(ShiftReconciliation.id == reconciliation_id)
        .first()
    )
    if not reconciliation:
        return None
    drawer = (
        db.query(DrawerSession)
        .filter(DrawerSession.id == reconciliation.drawer_session_id)
        .first()
    )
    operator = None
    closer = None
    if drawer:
        operator = drawer.user
        closer = reconciliation.closed_by_user

    payment_rows = (
        db.query(
            Payment.payment_method,
            func.count(Payment.id),
            func.coalesce(func.sum(Payment.amount), 0.0),
        )
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.drawer_session_id == reconciliation.drawer_session_id)
        .group_by(Payment.payment_method)
        .order_by(Payment.payment_method.asc())
        .all()
    )

    return {
        "reconciliation": reconciliation,
        "drawer": drawer,
        "operator_name": operator.full_name if operator else None,
        "closed_by_name": closer.full_name if closer else None,
        "payment_breakdown": [
            {
                "payment_method": row[0],
                "count": int(row[1]),
                "amount": float(row[2]),
            }
            for row in payment_rows
        ],
    }


def get_daily_close_data(db: Session, report_date: Optional[datetime]) -> dict:
    """All shift reconciliations closed on a given day + day totals."""
    if report_date is None:
        report_date = datetime.now().astimezone()
    start = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    shifts = (
        db.query(ShiftReconciliation)
        .join(DrawerSession, DrawerSession.id == ShiftReconciliation.drawer_session_id)
        .filter(
            DrawerSession.closed_at.isnot(None),
            DrawerSession.closed_at >= start,
            DrawerSession.closed_at < end,
        )
        .order_by(DrawerSession.closed_at.asc())
        .all()
    )

    totals = {
        "gross_sales_total": 0.0,
        "net_sales_total": 0.0,
        "cash_sales_total": 0.0,
        "non_cash_sales_total": 0.0,
        "refunds_total": 0.0,
        "cash_variance": 0.0,
        "non_cash_variance": 0.0,
        "completed_order_count": 0,
        "shift_count": len(shifts),
    }
    for shift in shifts:
        totals["gross_sales_total"] += float(shift.gross_sales_total or 0)
        totals["net_sales_total"] += float(shift.net_sales_total or 0)
        totals["cash_sales_total"] += float(shift.cash_sales_total or 0)
        totals["non_cash_sales_total"] += float(shift.non_cash_sales_total or 0)
        totals["refunds_total"] += float(shift.refunds_total or 0)
        totals["cash_variance"] += float(shift.cash_variance or 0)
        totals["non_cash_variance"] += float(shift.non_cash_variance or 0)
        totals["completed_order_count"] += int(shift.completed_order_count or 0)

    return {"date": report_date.date().isoformat(), "totals": totals, "shifts": shifts}


def get_sales_summary_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    cashier_id: Optional[int] = None,
) -> dict:
    sales_query = db.query(
        func.coalesce(
            func.sum(func.coalesce(Order.subtotal_amount, Order.total_amount)), 0.0
        ),
        func.coalesce(func.sum(Order.discount_amount), 0.0),
        func.coalesce(func.sum(Order.total_amount), 0.0),
        func.count(Order.id),
    ).filter(Order.status == "completed")
    refunds_query = (
        db.query(func.coalesce(func.sum(Refund.total_amount), 0.0))
        .join(Order, Refund.order_id == Order.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        sales_query = sales_query.filter(Order.created_at >= start_date)
        refunds_query = refunds_query.filter(Refund.created_at >= start_date)
    if end_date:
        sales_query = sales_query.filter(Order.created_at <= end_date)
        refunds_query = refunds_query.filter(Refund.created_at <= end_date)
    if cashier_id:
        sales_query = sales_query.filter(Order.user_id == cashier_id)
        refunds_query = refunds_query.filter(Order.user_id == cashier_id)

    gross_revenue, total_discounts, total_revenue, order_count = sales_query.first()
    total_refunds = float(refunds_query.scalar() or 0.0)
    net_revenue = float(total_revenue or 0.0) - total_refunds
    average_order_value = total_revenue / order_count if order_count > 0 else 0.0

    return {
        "gross_revenue": float(gross_revenue),
        "total_discounts": float(total_discounts),
        "total_revenue": float(total_revenue),
        "total_refunds": total_refunds,
        "net_revenue": net_revenue,
        "order_count": int(order_count),
        "average_order_value": float(average_order_value),
    }


def get_top_products_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
):
    query = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.sku.label("product_sku"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
        )
        .select_from(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    return (
        query.group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )


def get_category_sales_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = (
        db.query(
            Category.id.label("category_id"),
            func.coalesce(Category.name, "Uncategorized").label("category_name"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
        )
        .select_from(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    return (
        query.group_by(Category.id, Category.name)
        .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
        .all()
    )


def get_low_stock_products_data(
    db: Session,
    threshold: Optional[int] = None,
):
    """Products at or below stock threshold.

    When threshold is None, use each product's own reorder_point (falling
    back to min_stock), and a default of 10 when both are unset/zero.
    """
    query = db.query(Product)
    if threshold is not None:
        query = query.filter(Product.stock_quantity <= threshold)
    else:
        effective_threshold = func.coalesce(
            func.nullif(
                case(
                    (
                        Product.reorder_point >= Product.min_stock,
                        Product.reorder_point,
                    ),
                    else_=Product.min_stock,
                ),
                0,
            ),
            10,
        )
        query = query.filter(Product.stock_quantity <= effective_threshold)
    return query.order_by(Product.stock_quantity.asc()).all()


def get_top_customers_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
):
    query = (
        db.query(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            Customer.email.label("customer_email"),
            Customer.points_balance.label("points_balance"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    return (
        query.group_by(
            Customer.id, Customer.name, Customer.email, Customer.points_balance
        )
        .order_by(func.sum(Order.total_amount).desc())
        .limit(limit)
        .all()
    )


def get_invoice_summary_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    supplier_id: Optional[int] = None,
) -> dict:
    query = db.query(PurchaseInvoice)
    if start_date:
        query = query.filter(PurchaseInvoice.created_at >= start_date)
    if end_date:
        query = query.filter(PurchaseInvoice.created_at <= end_date)
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)

    rows = query.with_entities(
        func.count(PurchaseInvoice.id),
        func.coalesce(
            func.sum(
                case(
                    (
                        PurchaseInvoice.status == "approved",
                        PurchaseInvoice.total_amount,
                    ),
                    else_=0.0,
                )
            ),
            0.0,
        ),
        func.coalesce(func.sum(PurchaseInvoice.total_amount), 0.0),
        func.coalesce(func.sum(PurchaseInvoice.variance_amount), 0.0),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "approved", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "rejected", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "pending_review", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "draft", 1), else_=0)),
            0,
        ),
    ).first()

    (
        invoice_count,
        approved_total,
        billed_total,
        variance_total,
        approved_count,
        rejected_count,
        pending_review_count,
        draft_count,
    ) = rows

    return {
        "invoice_count": int(invoice_count or 0),
        "approved_count": int(approved_count or 0),
        "rejected_count": int(rejected_count or 0),
        "pending_review_count": int(pending_review_count or 0),
        "draft_count": int(draft_count or 0),
        "approved_total": float(approved_total or 0.0),
        "billed_total": float(billed_total or 0.0),
        "variance_total": float(variance_total or 0.0),
    }


def get_executive_summary_data(
    db: Session,
    invoice_summary: Optional[dict] = None,
) -> dict:
    active_customers_count = (
        db.query(func.count(Customer.id))
        .filter(Customer.is_active == True)  # noqa: E712
        .scalar()
    )
    raw_points_issued = (
        db.query(func.coalesce(func.sum(LoyaltyTransaction.points_delta), 0))
        .filter(LoyaltyTransaction.points_delta > 0)
        .scalar()
    )
    raw_points_redeemed = (
        db.query(func.coalesce(func.sum(LoyaltyTransaction.points_delta), 0))
        .filter(
            LoyaltyTransaction.transaction_type == "redeem",
            LoyaltyTransaction.points_delta < 0,
        )
        .scalar()
    )
    open_purchase_orders_count = (
        db.query(func.count(PurchaseOrder.id))
        .filter(PurchaseOrder.status.in_(("draft", "ordered", "partially_received")))
        .scalar()
    )
    received_value_expr = (
        PurchaseOrderItem.quantity_received * PurchaseOrderItem.unit_cost
    )
    raw_purchase_received_value = db.query(
        func.coalesce(
            func.sum(received_value_expr),
            0.0,
        )
    ).scalar()
    reconciled_shift_count = db.query(func.count(ShiftReconciliation.id)).scalar()
    raw_avg_cash_variance = db.query(
        func.coalesce(func.avg(ShiftReconciliation.cash_variance), 0.0)
    ).scalar()

    summary = {
        "active_customers_count": int(
            active_customers_count if active_customers_count is not None else 0
        ),
        "points_issued": int(raw_points_issued if raw_points_issued is not None else 0),
        "points_redeemed": int(
            abs(raw_points_redeemed) if raw_points_redeemed is not None else 0
        ),
        "open_purchase_orders_count": int(
            open_purchase_orders_count if open_purchase_orders_count is not None else 0
        ),
        "purchase_received_value": float(
            raw_purchase_received_value
            if raw_purchase_received_value is not None
            else 0.0
        ),
        "reconciled_shift_count": int(
            reconciled_shift_count if reconciled_shift_count is not None else 0
        ),
        "average_cash_variance": float(
            raw_avg_cash_variance if raw_avg_cash_variance is not None else 0.0
        ),
    }

    if invoice_summary:
        summary.update(
            {
                "invoice_count": invoice_summary["invoice_count"],
                "invoice_pending_review_count": invoice_summary["pending_review_count"],
                "invoice_approved_total": invoice_summary["approved_total"],
                "invoice_billed_total": invoice_summary["billed_total"],
                "invoice_variance_total": invoice_summary["variance_total"],
            }
        )

    return summary
