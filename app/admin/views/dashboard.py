from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import joinedload

from app.core.localization import format_currency, get_localization_setting
from app.models.customer import Customer
from app.models.drawer import DrawerSession
from app.models.order import Order
from app.models.product import Category, Product
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseOrder,
    Supplier,
    SupplierPayment,
)
from app.models.stock_movement import StockMovement
from app.models.tenant import Tenant
from app.services.reports import (
    get_executive_summary_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_supplier_payment_summary_data,
    get_top_customers_data,
    get_top_products_data,
)


def _period_start(period: str) -> tuple[datetime | None, datetime | None]:
    now = datetime.now(UTC)
    if period == "today":
        start = datetime(year=now.year, month=now.month, day=now.day, tzinfo=UTC)
    elif period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "month":
        start = datetime(year=now.year, month=now.month, day=1, tzinfo=UTC)
    else:
        start = None
    return start, None


def build_dashboard_data(db, tenant_id: int, period: str = "30d") -> dict:
    period = period if period in ("today", "7d", "30d", "month", "all") else "30d"
    start_date, end_date = _period_start(period)
    # Normalize to tenant-scoped queries
    sales_summary = get_sales_summary_data(
        db=db, start_date=start_date, end_date=end_date, tenant_id=tenant_id
    )
    top_products = get_top_products_data(
        db=db, start_date=start_date, end_date=end_date, limit=5, tenant_id=tenant_id
    )
    low_stock_products = get_low_stock_products_data(db=db, tenant_id=tenant_id)
    top_customers = get_top_customers_data(
        db=db, start_date=start_date, end_date=end_date, limit=5, tenant_id=tenant_id
    )
    invoice_summary = get_invoice_summary_data(
        db=db, start_date=start_date, end_date=end_date, tenant_id=tenant_id
    )
    payment_summary = get_supplier_payment_summary_data(
        db=db, start_date=start_date, end_date=end_date, tenant_id=tenant_id
    )
    executive_summary = get_executive_summary_data(
        db=db, invoice_summary=invoice_summary, tenant_id=tenant_id
    )
    localization = get_localization_setting(db, tenant_id)

    # Workflow counts (same as WorkflowsAdmin hub, unified low-stock)
    from app.core.replenishment import build_replenishment_suggestions

    all_products = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    low_stock_count = sum(
        1
        for s in build_replenishment_suggestions(db, all_products, lookback_days=30)
        if s.should_reorder
    )
    draft_po_count = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.status == "draft", PurchaseOrder.tenant_id == tenant_id)
        .count()
    )
    pending_invoice_count = (
        db.query(PurchaseInvoice)
        .filter(
            PurchaseInvoice.status == "pending_review",
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .count()
    )
    pending_payment_count = (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.status == "pending_review",
            SupplierPayment.tenant_id == tenant_id,
        )
        .count()
    )
    open_drawer_count = (
        db.query(DrawerSession)
        .filter(DrawerSession.status == "open", DrawerSession.tenant_id == tenant_id)
        .count()
    )

    recent_orders = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(Order.tenant_id == tenant_id)
        .order_by(Order.id.desc())
        .limit(5)
        .all()
    )
    recent_movements = (
        db.query(StockMovement)
        .options(joinedload(StockMovement.product))
        .filter(StockMovement.tenant_id == tenant_id)
        .order_by(StockMovement.id.desc())
        .limit(5)
        .all()
    )

    # Onboarding checklist for new tenants (intuitive flow)
    has_products = len(all_products) > 0
    has_categories = (
        db.query(Category).filter(Category.tenant_id == tenant_id).count() > 0
    )
    has_suppliers = (
        db.query(Supplier).filter(Supplier.tenant_id == tenant_id).count() > 0
    )
    has_customers = (
        db.query(Customer).filter(Customer.tenant_id == tenant_id).count() > 0
    )
    has_orders = db.query(Order).filter(Order.tenant_id == tenant_id).count() > 0
    onboarding_complete = all(
        [has_products, has_categories, has_suppliers, has_customers, has_orders]
    )

    localized = {
        "net_revenue": format_currency(
            float(sales_summary["net_revenue"]),
            localization.currency,
            localization.number_format,
        ),
        "total_refunds": format_currency(
            float(sales_summary["total_refunds"]),
            localization.currency,
            localization.number_format,
        ),
        "average_order_value": format_currency(
            float(sales_summary["average_order_value"]),
            localization.currency,
            localization.number_format,
        ),
        "gross_revenue": format_currency(
            float(sales_summary["gross_revenue"]),
            localization.currency,
            localization.number_format,
        ),
        "total_discounts": format_currency(
            float(sales_summary["total_discounts"]),
            localization.currency,
            localization.number_format,
        ),
    }

    top_products_view = [
        {
            "product_name": row.product_name,
            "product_sku": row.product_sku,
            "total_quantity_sold": row.total_quantity_sold,
            "total_revenue_formatted": format_currency(
                float(row.total_revenue or 0.0),
                localization.currency,
                localization.number_format,
            ),
        }
        for row in top_products
    ]

    return {
        "period": period,
        "period_label": {
            "today": "Today",
            "7d": "Last 7 Days",
            "30d": "Last 30 Days",
            "month": "This Month",
            "all": "All Time",
        }[period],
        "localization": localization,
        "localized": localized,
        "sales_summary": sales_summary,
        "top_products": top_products_view,
        "low_stock_products": low_stock_products,
        "low_stock_count": low_stock_count,
        "top_customers": top_customers,
        "executive_summary": executive_summary,
        "invoice_summary": invoice_summary,
        "payment_summary": payment_summary,
        "draft_po_count": draft_po_count,
        "pending_invoice_count": pending_invoice_count,
        "pending_payment_count": pending_payment_count,
        "open_drawer_count": open_drawer_count,
        "recent_orders": recent_orders,
        "recent_movements": recent_movements,
        "onboarding": {
            "has_products": has_products,
            "has_categories": has_categories,
            "has_suppliers": has_suppliers,
            "has_customers": has_customers,
            "has_orders": has_orders,
            "complete": onboarding_complete,
        },
    }


def get_tenant_switcher_context(db, current_tenant_id: int) -> dict:
    tenants = db.query(Tenant).order_by(Tenant.id.asc()).all()
    current = next((t for t in tenants if t.id == current_tenant_id), None)
    return {
        "tenants": tenants,
        "current_tenant": current,
        "current_tenant_id": current_tenant_id,
    }
