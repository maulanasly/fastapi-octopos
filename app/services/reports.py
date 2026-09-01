from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.replenishment import build_replenishment_suggestions
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Category, Product
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
)
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation


def get_shift_report_data(
    db: Session,
    reconciliation_id: int,
    tenant_id: int | None = None,
) -> dict:
    """Full shift report for one drawer reconciliation."""
    reconciliation_query = db.query(ShiftReconciliation).filter(
        ShiftReconciliation.id == reconciliation_id
    )
    if tenant_id is not None:
        reconciliation_query = reconciliation_query.filter(
            ShiftReconciliation.tenant_id == tenant_id
        )
    reconciliation = reconciliation_query.first()
    if not reconciliation:
        return None
    drawer_query = db.query(DrawerSession).filter(
        DrawerSession.id == reconciliation.drawer_session_id
    )
    if tenant_id is not None:
        drawer_query = drawer_query.filter(DrawerSession.tenant_id == tenant_id)
    drawer = drawer_query.first()
    operator = None
    closer = None
    if drawer:
        operator = drawer.user
        closer = reconciliation.closed_by_user

    payment_query = (
        db.query(
            Payment.payment_method,
            func.count(Payment.id),
            func.coalesce(func.sum(Payment.amount), 0.0),
        )
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.drawer_session_id == reconciliation.drawer_session_id)
    )
    if tenant_id is not None:
        payment_query = payment_query.filter(Order.tenant_id == tenant_id)
    payment_rows = (
        payment_query.group_by(Payment.payment_method)
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


def get_daily_close_data(
    db: Session,
    report_date: datetime | None,
    tenant_id: int | None = None,
) -> dict:
    """All shift reconciliations closed on a given day + day totals.

    ``DrawerSession.closed_at`` is stored as naive UTC (SQLite); the local
    day's boundaries are converted to their UTC instants so the comparison
    stays correct near midnight in any timezone.
    """
    if report_date is None:
        report_date = datetime.now().astimezone()
    local_start = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start = local_start.astimezone(UTC).replace(tzinfo=None)
    end = (local_start + timedelta(days=1)).astimezone(UTC).replace(tzinfo=None)

    shifts_query = (
        db.query(ShiftReconciliation)
        .join(DrawerSession, DrawerSession.id == ShiftReconciliation.drawer_session_id)
        .filter(
            DrawerSession.closed_at.isnot(None),
            DrawerSession.closed_at >= start,
            DrawerSession.closed_at < end,
        )
    )
    if tenant_id is not None:
        shifts_query = shifts_query.filter(DrawerSession.tenant_id == tenant_id)
    shifts = shifts_query.order_by(DrawerSession.closed_at.asc()).all()

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
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    cashier_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    sales_query = db.query(
        func.coalesce(
            func.sum(func.coalesce(Order.subtotal_amount, Order.total_amount)), 0.0
        ),
        func.coalesce(func.sum(Order.discount_amount), 0.0),
        func.coalesce(func.sum(Order.total_amount), 0.0),
        func.count(Order.id),
    ).filter(Order.status.in_(["serving", "completed"]))
    refunds_query = (
        db.query(func.coalesce(func.sum(Refund.total_amount), 0.0))
        .join(Order, Refund.order_id == Order.id)
        .filter(Order.status.in_(["serving", "completed"]))
    )

    if tenant_id is not None:
        sales_query = sales_query.filter(Order.tenant_id == tenant_id)
        refunds_query = refunds_query.filter(Refund.tenant_id == tenant_id)
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

    # Per-sale COGS from the cost snapshot on each line (migration 0020).
    # Shares the revenue query's status/window/cashier filters so the
    # margin is computed over exactly the same orders as net_revenue;
    # refunds reverse cost against the same order set.
    sold_filters = [Order.status.in_(["serving", "completed"])]
    if tenant_id is not None:
        sold_filters.append(Order.tenant_id == tenant_id)
        sold_filters.append(OrderItem.tenant_id == tenant_id)
    if start_date:
        sold_filters.append(Order.created_at >= start_date)
    if end_date:
        sold_filters.append(Order.created_at <= end_date)
    if cashier_id:
        sold_filters.append(Order.user_id == cashier_id)

    known_sold_qty, gross_known_cogs = (
        db.query(
            func.coalesce(func.sum(OrderItem.quantity), 0),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_cost), 0.0),
        )
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(OrderItem.unit_cost.is_not(None), *sold_filters)
        .first()
    )
    total_sold_qty = (
        db.query(func.coalesce(func.sum(OrderItem.quantity), 0))
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(*sold_filters)
        .scalar()
    )

    # Refunds reverse cost only for lines whose cost is known.
    refunded_filters = [*sold_filters]
    if tenant_id is not None:
        refunded_filters.append(RefundItem.tenant_id == tenant_id)
    refunded_qty, refunded_cogs = (
        db.query(
            func.coalesce(func.sum(RefundItem.quantity), 0),
            func.coalesce(func.sum(RefundItem.quantity * OrderItem.unit_cost), 0.0),
        )
        .select_from(RefundItem)
        .join(OrderItem, RefundItem.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(OrderItem.unit_cost.is_not(None), *refunded_filters)
        .first()
    )

    known_sold_qty = int(known_sold_qty or 0)
    total_sold_qty = int(total_sold_qty or 0)
    gross_known_cogs = float(gross_known_cogs or 0.0)
    refunded_qty = int(refunded_qty or 0)
    refunded_cogs = float(refunded_cogs or 0.0)

    cogs_total = round(max(gross_known_cogs - refunded_cogs, 0.0), 2)
    # Coverage of the COGS basis: share of sold quantity that carried a
    # cost snapshot. Clamped so refunds can never push it above 100%.
    cogs_known_ratio = (
        round(min(known_sold_qty / total_sold_qty, 1.0), 4)
        if total_sold_qty > 0
        else None
    )
    gross_margin_amount = round(net_revenue - cogs_total, 2)
    gross_margin_percent = (
        round(gross_margin_amount / net_revenue * 100, 2) if net_revenue > 0 else None
    )
    gross_margin_amount = round(net_revenue - cogs_total, 2)
    gross_margin_percent = (
        round(gross_margin_amount / net_revenue * 100, 2) if net_revenue > 0 else None
    )

    return {
        "gross_revenue": float(gross_revenue),
        "total_discounts": float(total_discounts),
        "total_revenue": float(total_revenue),
        "total_refunds": total_refunds,
        "net_revenue": net_revenue,
        "order_count": int(order_count),
        "average_order_value": float(average_order_value),
        "cogs_total": cogs_total,
        "gross_margin_amount": gross_margin_amount,
        "gross_margin_percent": gross_margin_percent,
        "cogs_known_ratio": cogs_known_ratio,
    }


def get_top_products_data(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
    tenant_id: int | None = None,
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
        .filter(Order.status.in_(["serving", "completed"]))
    )

    if tenant_id is not None:
        query = query.filter(
            Order.tenant_id == tenant_id,
            OrderItem.tenant_id == tenant_id,
            Product.tenant_id == tenant_id,
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
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    tenant_id: int | None = None,
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
        .filter(Order.status.in_(["serving", "completed"]))
    )

    if tenant_id is not None:
        query = query.filter(
            Order.tenant_id == tenant_id,
            OrderItem.tenant_id == tenant_id,
            Product.tenant_id == tenant_id,
            Category.tenant_id == tenant_id,
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
    threshold: int | None = None,
    tenant_id: int | None = None,
):
    """Products at or below stock threshold.

    When threshold is provided, simple stock <= threshold.
    When None, unified with replenishment.should_reorder (lead-time
    projection, min_stock, reorder_point).
    """
    query = db.query(Product)
    if tenant_id is not None:
        query = query.filter(Product.tenant_id == tenant_id)
    if threshold is not None:
        query = query.filter(Product.stock_quantity <= threshold)
        return query.order_by(Product.stock_quantity.asc()).all()
    # Unified: use replenishment logic for intuitive low-stock
    products = query.all()
    suggestions = build_replenishment_suggestions(
        db=db, products=products, lookback_days=30
    )
    low_ids = {s.product_id for s in suggestions if s.should_reorder}
    if not low_ids:
        return []
    # Preserve stock-asc order for UI
    return sorted(
        [p for p in products if p.id in low_ids],
        key=lambda p: p.stock_quantity,
    )


def get_top_customers_data(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
    tenant_id: int | None = None,
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
        .filter(Order.status.in_(["serving", "completed"]))
    )

    if tenant_id is not None:
        query = query.filter(
            Customer.tenant_id == tenant_id,
            Order.tenant_id == tenant_id,
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
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    query = db.query(PurchaseInvoice)
    if tenant_id is not None:
        query = query.filter(PurchaseInvoice.tenant_id == tenant_id)
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


def get_supplier_payment_summary_data(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    payment_query = db.query(SupplierPayment)
    if tenant_id is not None:
        payment_query = payment_query.filter(SupplierPayment.tenant_id == tenant_id)
    if start_date:
        payment_query = payment_query.filter(SupplierPayment.created_at >= start_date)
    if end_date:
        payment_query = payment_query.filter(SupplierPayment.created_at <= end_date)
    if supplier_id:
        payment_query = payment_query.filter(SupplierPayment.supplier_id == supplier_id)

    rows = payment_query.with_entities(
        func.count(SupplierPayment.id),
        func.coalesce(
            func.sum(
                case(
                    (SupplierPayment.status == "approved", SupplierPayment.amount),
                    else_=0.0,
                )
            ),
            0.0,
        ),
        func.coalesce(
            func.sum(case((SupplierPayment.status == "approved", 1), else_=0)), 0
        ),
        func.coalesce(
            func.sum(case((SupplierPayment.status == "rejected", 1), else_=0)), 0
        ),
        func.coalesce(
            func.sum(case((SupplierPayment.status == "pending_review", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((SupplierPayment.status == "draft", 1), else_=0)), 0
        ),
    ).first()

    (
        payment_count,
        approved_total,
        approved_count,
        rejected_count,
        pending_review_count,
        draft_count,
    ) = rows

    invoice_query = db.query(PurchaseInvoice)
    if tenant_id is not None:
        invoice_query = invoice_query.filter(PurchaseInvoice.tenant_id == tenant_id)
    if start_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.created_at >= start_date)
    if end_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.created_at <= end_date)
    if supplier_id:
        invoice_query = invoice_query.filter(PurchaseInvoice.supplier_id == supplier_id)

    approved_invoice_total = invoice_query.with_entities(
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
        )
    ).scalar()

    return {
        "payment_count": int(payment_count or 0),
        "approved_count": int(approved_count or 0),
        "rejected_count": int(rejected_count or 0),
        "pending_review_count": int(pending_review_count or 0),
        "draft_count": int(draft_count or 0),
        "approved_total": float(approved_total or 0.0),
        "outstanding_payable": float(
            float(approved_invoice_total or 0.0) - float(approved_total or 0.0)
        ),
    }


def get_executive_summary_data(
    db: Session,
    invoice_summary: dict | None = None,
    tenant_id: int | None = None,
) -> dict:
    customers_query = db.query(func.count(Customer.id)).filter(
        Customer.is_active == True  # noqa: E712
    )
    points_issued_query = db.query(
        func.coalesce(func.sum(LoyaltyTransaction.points_delta), 0)
    ).filter(LoyaltyTransaction.points_delta > 0)
    points_redeemed_query = db.query(
        func.coalesce(func.sum(LoyaltyTransaction.points_delta), 0)
    ).filter(
        LoyaltyTransaction.transaction_type == "redeem",
        LoyaltyTransaction.points_delta < 0,
    )
    open_pos_query = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(("draft", "ordered", "partially_received"))
    )
    received_value_expr = (
        PurchaseOrderItem.quantity_received * PurchaseOrderItem.unit_cost
    )
    purchase_received_query = db.query(
        func.coalesce(
            func.sum(received_value_expr),
            0.0,
        )
    )
    reconciled_shifts_query = db.query(func.count(ShiftReconciliation.id))
    avg_cash_variance_query = db.query(
        func.coalesce(func.avg(ShiftReconciliation.cash_variance), 0.0)
    )

    if tenant_id is not None:
        customers_query = customers_query.filter(Customer.tenant_id == tenant_id)
        points_issued_query = points_issued_query.filter(
            LoyaltyTransaction.tenant_id == tenant_id
        )
        points_redeemed_query = points_redeemed_query.filter(
            LoyaltyTransaction.tenant_id == tenant_id
        )
        open_pos_query = open_pos_query.filter(PurchaseOrder.tenant_id == tenant_id)
        purchase_received_query = purchase_received_query.filter(
            PurchaseOrderItem.tenant_id == tenant_id
        )
        reconciled_shifts_query = reconciled_shifts_query.filter(
            ShiftReconciliation.tenant_id == tenant_id
        )
        avg_cash_variance_query = avg_cash_variance_query.filter(
            ShiftReconciliation.tenant_id == tenant_id
        )

    active_customers_count = customers_query.scalar()
    raw_points_issued = points_issued_query.scalar()
    raw_points_redeemed = points_redeemed_query.scalar()
    open_purchase_orders_count = open_pos_query.scalar()
    raw_purchase_received_value = purchase_received_query.scalar()
    reconciled_shift_count = reconciled_shifts_query.scalar()
    raw_avg_cash_variance = avg_cash_variance_query.scalar()

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


def get_shift_list_data(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    tenant_id: int | None = None,
) -> list[dict]:
    """Recent reconciled shifts (newest first) with operator details."""
    query = (
        db.query(ShiftReconciliation)
        .join(DrawerSession, DrawerSession.id == ShiftReconciliation.drawer_session_id)
        .filter(DrawerSession.closed_at.isnot(None))
    )
    if tenant_id is not None:
        query = query.filter(DrawerSession.tenant_id == tenant_id)
    if date_from is not None:
        query = query.filter(DrawerSession.closed_at >= date_from)
    if date_to is not None:
        query = query.filter(DrawerSession.closed_at <= date_to)
    rows = (
        query.order_by(DrawerSession.closed_at.desc()).offset(skip).limit(limit).all()
    )
    items = []
    for rec in rows:
        drawer_query = db.query(DrawerSession).filter(
            DrawerSession.id == rec.drawer_session_id
        )
        if tenant_id is not None:
            drawer_query = drawer_query.filter(DrawerSession.tenant_id == tenant_id)
        drawer = drawer_query.first()
        items.append(
            {
                "reconciliation_id": rec.id,
                "drawer_session_id": rec.drawer_session_id,
                "opened_at": drawer.opened_at if drawer else None,
                "closed_at": drawer.closed_at if drawer else None,
                "operator_name": drawer.user.full_name
                if drawer and drawer.user
                else None,
                "cash_sales_total": float(rec.cash_sales_total or 0.0),
                "non_cash_sales_total": float(rec.non_cash_sales_total or 0.0),
                "refunds_total": float(rec.refunds_total or 0.0),
                "gross_sales_total": float(rec.gross_sales_total or 0.0),
                "net_sales_total": float(rec.net_sales_total or 0.0),
                "completed_order_count": int(rec.completed_order_count or 0),
                "cash_variance": float(rec.cash_variance or 0.0),
            }
        )
    return items


def get_supplier_spend_data(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    tenant_id: int | None = None,
) -> dict:
    """Spend by supplier over a window + COGS estimate (approved invoices)."""
    invoice_query = db.query(
        PurchaseInvoice.supplier_id,
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
        func.coalesce(func.sum(PurchaseInvoice.variance_amount), 0.0),
    )
    if tenant_id is not None:
        invoice_query = invoice_query.filter(PurchaseInvoice.tenant_id == tenant_id)
    if start_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.created_at >= start_date)
    if end_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.created_at <= end_date)
    invoice_rows = invoice_query.group_by(PurchaseInvoice.supplier_id).all()

    po_query = db.query(PurchaseOrder.supplier_id, func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status != "cancelled"
    )
    if tenant_id is not None:
        po_query = po_query.filter(PurchaseOrder.tenant_id == tenant_id)
    if start_date:
        po_query = po_query.filter(PurchaseOrder.created_at >= start_date)
    if end_date:
        po_query = po_query.filter(PurchaseOrder.created_at <= end_date)
    po_counts = {
        supplier_id: count
        for supplier_id, count in po_query.group_by(PurchaseOrder.supplier_id).all()
    }

    supplier_ids = {row[0] for row in invoice_rows} | set(po_counts)
    names: dict[int, str] = {}
    if supplier_ids:
        names = dict(
            db.query(Supplier.id, Supplier.name)
            .filter(Supplier.id.in_(supplier_ids))
            .all()
        )

    items = []
    cogs_estimate = 0.0
    for supplier_id, invoice_count, approved_total, variance_total in invoice_rows:
        approved_total = float(approved_total or 0.0)
        cogs_estimate += approved_total
        items.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": names.get(supplier_id, f"Supplier {supplier_id}"),
                "po_count": int(po_counts.get(supplier_id, 0)),
                "invoice_count": int(invoice_count or 0),
                "approved_total": approved_total,
                "variance_total": float(variance_total or 0.0),
            }
        )
    item_supplier_ids = {item["supplier_id"] for item in items}
    for supplier_id, po_count in po_counts.items():
        if supplier_id in item_supplier_ids:
            continue
        items.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": names.get(supplier_id, f"Supplier {supplier_id}"),
                "po_count": int(po_count),
                "invoice_count": 0,
                "approved_total": 0.0,
                "variance_total": 0.0,
            }
        )
    items.sort(key=lambda item: item["approved_total"], reverse=True)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "cogs_estimate": round(cogs_estimate, 2),
        "items": items,
    }


def get_variance_trend_data(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    tenant_id: int | None = None,
) -> dict:
    """Monthly purchase-invoice variance trend (dialect-safe Python grouping)."""
    query = db.query(
        PurchaseInvoice.created_at,
        PurchaseInvoice.total_amount,
        PurchaseInvoice.variance_amount,
        PurchaseInvoice.status,
    )
    if tenant_id is not None:
        query = query.filter(PurchaseInvoice.tenant_id == tenant_id)
    if start_date:
        query = query.filter(PurchaseInvoice.created_at >= start_date)
    if end_date:
        query = query.filter(PurchaseInvoice.created_at <= end_date)

    months: dict[str, dict] = {}
    for created_at, total_amount, variance_amount, status in query.all():
        period = created_at.strftime("%Y-%m")
        bucket = months.setdefault(
            period,
            {
                "period": period,
                "invoice_count": 0,
                "billed_total": 0.0,
                "approved_total": 0.0,
                "variance_total": 0.0,
            },
        )
        bucket["invoice_count"] += 1
        bucket["billed_total"] += float(total_amount or 0)
        bucket["variance_total"] += float(variance_amount or 0)
        if status == "approved":
            bucket["approved_total"] += float(total_amount or 0)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "months": [months[key] for key in sorted(months)],
    }
