from datetime import datetime, timedelta, timezone

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, ModelView, expose
from sqlalchemy import case, func

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.core.database import SessionLocal
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.stock_movement import StockMovement
from app.models.sync_event import SyncEventLog
from app.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
    ]
    column_searchable_list = [User.email, User.full_name]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.description]
    column_searchable_list = [Category.name]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.price,
        Product.stock_quantity,
        Product.min_stock,
        Product.max_stock,
        Product.reorder_point,
        Product.lead_time_days,
        Product.category,
    ]
    column_searchable_list = [Product.name, Product.sku]
    column_sortable_list = [
        Product.price,
        Product.stock_quantity,
        Product.reorder_point,
        Product.lead_time_days,
    ]


class PromotionAdmin(ModelView, model=Promotion):
    column_list = [
        Promotion.id,
        Promotion.code,
        Promotion.name,
        Promotion.discount_type,
        Promotion.discount_value,
        Promotion.applies_to,
        Promotion.is_active,
        Promotion.usage_count,
        Promotion.usage_limit,
        Promotion.starts_at,
        Promotion.ends_at,
    ]
    column_searchable_list = [Promotion.code, Promotion.name, Promotion.description]
    column_sortable_list = [Promotion.id, Promotion.usage_count, Promotion.starts_at]


class CustomerAdmin(ModelView, model=Customer):
    column_list = [
        Customer.id,
        Customer.name,
        Customer.email,
        Customer.phone,
        Customer.points_balance,
        Customer.is_active,
        Customer.created_at,
    ]
    column_searchable_list = [Customer.name, Customer.email, Customer.phone]
    column_sortable_list = [Customer.id, Customer.points_balance, Customer.created_at]


class LoyaltyTransactionAdmin(ModelView, model=LoyaltyTransaction):
    column_list = [
        LoyaltyTransaction.id,
        LoyaltyTransaction.customer,
        LoyaltyTransaction.order_id,
        LoyaltyTransaction.transaction_type,
        LoyaltyTransaction.points_delta,
        LoyaltyTransaction.balance_after,
        LoyaltyTransaction.created_at,
    ]
    column_searchable_list = [
        LoyaltyTransaction.transaction_type,
        LoyaltyTransaction.note,
    ]
    column_sortable_list = [LoyaltyTransaction.id, LoyaltyTransaction.created_at]


class SupplierAdmin(ModelView, model=Supplier):
    column_list = [
        Supplier.id,
        Supplier.name,
        Supplier.contact_email,
        Supplier.phone,
        Supplier.is_active,
        Supplier.created_at,
    ]
    column_searchable_list = [Supplier.name, Supplier.contact_email, Supplier.phone]
    column_sortable_list = [Supplier.created_at, Supplier.id]


class PurchaseOrderAdmin(ModelView, model=PurchaseOrder):
    column_list = [
        PurchaseOrder.id,
        PurchaseOrder.supplier,
        PurchaseOrder.user,
        PurchaseOrder.status,
        PurchaseOrder.total_estimated_amount,
        PurchaseOrder.created_at,
        PurchaseOrder.ordered_at,
        PurchaseOrder.received_at,
    ]
    column_searchable_list = [PurchaseOrder.status]
    column_sortable_list = [PurchaseOrder.created_at, PurchaseOrder.received_at]


class PurchaseOrderItemAdmin(ModelView, model=PurchaseOrderItem):
    column_list = [
        PurchaseOrderItem.id,
        PurchaseOrderItem.purchase_order_id,
        PurchaseOrderItem.product,
        PurchaseOrderItem.quantity_ordered,
        PurchaseOrderItem.quantity_received,
        PurchaseOrderItem.unit_cost,
    ]
    column_searchable_list = [PurchaseOrderItem.purchase_order_id]
    column_sortable_list = [PurchaseOrderItem.id]


class PurchaseInvoiceAdmin(ModelView, model=PurchaseInvoice):
    column_list = [
        PurchaseInvoice.id,
        PurchaseInvoice.invoice_number,
        PurchaseInvoice.supplier,
        PurchaseInvoice.purchase_order,
        PurchaseInvoice.user,
        PurchaseInvoice.status,
        PurchaseInvoice.total_amount,
        PurchaseInvoice.variance_amount,
        PurchaseInvoice.has_quantity_variance,
        PurchaseInvoice.has_price_variance,
        PurchaseInvoice.created_at,
    ]
    column_searchable_list = [PurchaseInvoice.invoice_number, PurchaseInvoice.status]
    column_sortable_list = [
        PurchaseInvoice.created_at,
        PurchaseInvoice.total_amount,
        PurchaseInvoice.variance_amount,
    ]


class PurchaseInvoiceItemAdmin(ModelView, model=PurchaseInvoiceItem):
    column_list = [
        PurchaseInvoiceItem.id,
        PurchaseInvoiceItem.invoice_id,
        PurchaseInvoiceItem.purchase_order_item_id,
        PurchaseInvoiceItem.product,
        PurchaseInvoiceItem.billed_quantity,
        PurchaseInvoiceItem.billed_unit_cost,
        PurchaseInvoiceItem.expected_quantity,
        PurchaseInvoiceItem.expected_unit_cost,
        PurchaseInvoiceItem.quantity_variance,
        PurchaseInvoiceItem.price_variance,
        PurchaseInvoiceItem.line_total,
    ]
    column_searchable_list = [
        PurchaseInvoiceItem.invoice_id,
        PurchaseInvoiceItem.purchase_order_item_id,
    ]
    column_sortable_list = [PurchaseInvoiceItem.id, PurchaseInvoiceItem.line_total]


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user,
        Order.customer,
        Order.promotion,
        Order.subtotal_amount,
        Order.discount_amount,
        Order.redeemed_points,
        Order.total_amount,
        Order.status,
        Order.created_at,
    ]
    column_sortable_list = [Order.created_at, Order.total_amount]
    column_searchable_list = [Order.id]


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
    ]
    column_searchable_list = [OrderItem.order_id]


class DrawerSessionAdmin(ModelView, model=DrawerSession):
    column_list = [
        DrawerSession.id,
        DrawerSession.user,
        DrawerSession.opened_at,
        DrawerSession.closed_at,
        DrawerSession.starting_cash,
        DrawerSession.ending_cash,
        DrawerSession.status,
    ]
    column_searchable_list = [DrawerSession.status]
    column_sortable_list = [DrawerSession.opened_at, DrawerSession.closed_at]


class ShiftReconciliationAdmin(ModelView, model=ShiftReconciliation):
    column_list = [
        ShiftReconciliation.id,
        ShiftReconciliation.drawer_session_id,
        ShiftReconciliation.closed_by_user,
        ShiftReconciliation.expected_cash,
        ShiftReconciliation.counted_cash,
        ShiftReconciliation.cash_variance,
        ShiftReconciliation.expected_non_cash,
        ShiftReconciliation.counted_non_cash,
        ShiftReconciliation.non_cash_variance,
        ShiftReconciliation.created_at,
    ]
    column_searchable_list = [ShiftReconciliation.drawer_session_id]
    column_sortable_list = [ShiftReconciliation.created_at, ShiftReconciliation.id]


class RefundAdmin(ModelView, model=Refund):
    column_list = [
        Refund.id,
        Refund.order_id,
        Refund.user,
        Refund.total_amount,
        Refund.created_at,
    ]
    column_searchable_list = [Refund.order_id]
    column_sortable_list = [Refund.created_at, Refund.total_amount]


class RefundItemAdmin(ModelView, model=RefundItem):
    column_list = [
        RefundItem.id,
        RefundItem.refund_id,
        RefundItem.order_item_id,
        RefundItem.product,
        RefundItem.quantity,
        RefundItem.unit_price,
    ]
    column_searchable_list = [RefundItem.refund_id, RefundItem.order_item_id]


class StockMovementAdmin(ModelView, model=StockMovement):
    column_list = [
        StockMovement.id,
        StockMovement.product,
        StockMovement.user,
        StockMovement.movement_type,
        StockMovement.quantity_before,
        StockMovement.quantity_delta,
        StockMovement.quantity_after,
        StockMovement.order_id,
        StockMovement.refund_id,
        StockMovement.created_at,
    ]
    column_searchable_list = [StockMovement.movement_type, StockMovement.note]
    column_sortable_list = [StockMovement.created_at, StockMovement.id]


class SyncEventLogAdmin(ModelView, model=SyncEventLog):
    column_list = [
        SyncEventLog.id,
        SyncEventLog.user,
        SyncEventLog.client_event_id,
        SyncEventLog.event_type,
        SyncEventLog.idempotency_key,
        SyncEventLog.status,
        SyncEventLog.resource_type,
        SyncEventLog.resource_id,
        SyncEventLog.processed_at,
    ]
    column_searchable_list = [
        SyncEventLog.client_event_id,
        SyncEventLog.event_type,
        SyncEventLog.idempotency_key,
        SyncEventLog.status,
    ]
    column_sortable_list = [SyncEventLog.processed_at, SyncEventLog.id]


class ReportsAdmin(BaseView):
    name = "Reports Dashboard"
    icon = "fa-solid fa-chart-line"

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            period = request.query_params.get("period", "30d")
            period_labels = {
                "today": "Today",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "month": "This Month",
                "all": "All Time",
            }
            if period == "today":
                start_date = datetime(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    tzinfo=timezone.utc,
                )
                end_date = None
            elif period == "7d":
                start_date = now - timedelta(days=7)
                end_date = None
            elif period == "30d":
                start_date = now - timedelta(days=30)
                end_date = None
            elif period == "month":
                start_date = datetime(
                    year=now.year,
                    month=now.month,
                    day=1,
                    tzinfo=timezone.utc,
                )
                end_date = None
            else:
                period = "all"
                start_date = None
                end_date = None

            # 1. Sales Summary
            summary_query = db.query(
                func.coalesce(
                    func.sum(func.coalesce(Order.subtotal_amount, Order.total_amount)),
                    0.0,
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
            if start_date is not None:
                summary_query = summary_query.filter(Order.created_at >= start_date)
                refunds_query = refunds_query.filter(Refund.created_at >= start_date)
            if end_date is not None:
                summary_query = summary_query.filter(Order.created_at <= end_date)
                refunds_query = refunds_query.filter(Refund.created_at <= end_date)

            (
                gross_revenue,
                total_discounts,
                total_revenue,
                order_count,
            ) = summary_query.first()
            raw_total_refunds = refunds_query.scalar()
            total_refunds = raw_total_refunds if raw_total_refunds is not None else 0.0
            net_revenue = float(total_revenue or 0.0) - float(total_refunds)
            average_order_value = (
                total_revenue / order_count if order_count > 0 else 0.0
            )
            sales_summary = {
                "gross_revenue": gross_revenue,
                "total_discounts": total_discounts,
                "total_revenue": total_revenue,
                "total_refunds": total_refunds,
                "net_revenue": net_revenue,
                "order_count": order_count,
                "average_order_value": average_order_value,
            }

            # 2. Top Selling Products
            top_products_query = (
                db.query(
                    Product.id.label("product_id"),
                    Product.name.label("product_name"),
                    Product.sku.label("product_sku"),
                    func.sum(OrderItem.quantity).label("total_quantity_sold"),
                    func.sum(OrderItem.quantity * OrderItem.unit_price).label(
                        "total_revenue"
                    ),
                )
                .select_from(OrderItem)
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .filter(Order.status == "completed")
            )
            if start_date is not None:
                top_products_query = top_products_query.filter(
                    Order.created_at >= start_date
                )
            if end_date is not None:
                top_products_query = top_products_query.filter(
                    Order.created_at <= end_date
                )
            top_products = (
                top_products_query.group_by(Product.id)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(10)
                .all()
            )

            # 3. Sales by Category
            category_sales_query = (
                db.query(
                    Category.id.label("category_id"),
                    func.coalesce(Category.name, "Uncategorized").label(
                        "category_name"
                    ),
                    func.sum(OrderItem.quantity).label("total_quantity_sold"),
                    func.sum(OrderItem.quantity * OrderItem.unit_price).label(
                        "total_revenue"
                    ),
                )
                .select_from(OrderItem)
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .outerjoin(Category, Product.category_id == Category.id)
                .filter(Order.status == "completed")
                .group_by(Category.id, Category.name)
                .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            )
            if start_date is not None:
                category_sales_query = category_sales_query.filter(
                    Order.created_at >= start_date
                )
            if end_date is not None:
                category_sales_query = category_sales_query.filter(
                    Order.created_at <= end_date
                )
            category_sales = category_sales_query.all()

            # 4. Low Stock Products (threshold <= 10)
            low_stock_products = (
                db.query(Product).filter(Product.stock_quantity <= 10).all()
            )

            # 5. Top Customers
            top_customers_query = (
                db.query(
                    Customer.id.label("customer_id"),
                    Customer.name.label("customer_name"),
                    Customer.email.label("customer_email"),
                    func.count(Order.id).label("order_count"),
                    func.coalesce(func.sum(Order.total_amount), 0.0).label(
                        "total_spent"
                    ),
                    Customer.points_balance.label("points_balance"),
                )
                .join(Order, Order.customer_id == Customer.id)
                .filter(Order.status == "completed")
            )
            if start_date is not None:
                top_customers_query = top_customers_query.filter(
                    Order.created_at >= start_date
                )
            if end_date is not None:
                top_customers_query = top_customers_query.filter(
                    Order.created_at <= end_date
                )
            top_customers = (
                top_customers_query.group_by(
                    Customer.id,
                    Customer.name,
                    Customer.email,
                    Customer.points_balance,
                )
                .order_by(func.sum(Order.total_amount).desc())
                .limit(5)
                .all()
            )

            invoice_summary_query = db.query(PurchaseInvoice)
            if start_date is not None:
                invoice_summary_query = invoice_summary_query.filter(
                    PurchaseInvoice.created_at >= start_date
                )
            if end_date is not None:
                invoice_summary_query = invoice_summary_query.filter(
                    PurchaseInvoice.created_at <= end_date
                )
            (
                invoice_count,
                invoice_pending_review_count,
                invoice_approved_total,
                invoice_billed_total,
                invoice_variance_total,
            ) = invoice_summary_query.with_entities(
                func.count(PurchaseInvoice.id),
                func.coalesce(
                    func.sum(
                        case((PurchaseInvoice.status == "pending_review", 1), else_=0)
                    ),
                    0,
                ),
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
            ).first()

            # 6. Executive Summary
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
                .filter(
                    PurchaseOrder.status.in_(("draft", "ordered", "partially_received"))
                )
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
            reconciled_shift_count = db.query(
                func.count(ShiftReconciliation.id)
            ).scalar()
            raw_avg_cash_variance = db.query(
                func.coalesce(func.avg(ShiftReconciliation.cash_variance), 0.0)
            ).scalar()

            executive_summary = {
                "gross_revenue": float(gross_revenue or 0.0),
                "total_discounts": float(total_discounts or 0.0),
                "active_customers_count": int(
                    active_customers_count if active_customers_count is not None else 0
                ),
                "points_issued": int(
                    raw_points_issued if raw_points_issued is not None else 0
                ),
                "points_redeemed": int(
                    abs(raw_points_redeemed) if raw_points_redeemed is not None else 0
                ),
                "open_purchase_orders_count": int(
                    open_purchase_orders_count
                    if open_purchase_orders_count is not None
                    else 0
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
                "invoice_count": int(invoice_count or 0),
                "invoice_pending_review_count": int(invoice_pending_review_count or 0),
                "invoice_approved_total": float(invoice_approved_total or 0.0),
                "invoice_billed_total": float(invoice_billed_total or 0.0),
                "invoice_variance_total": float(invoice_variance_total or 0.0),
            }

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "period": period,
                    "period_label": period_labels[period],
                    "sales_summary": sales_summary,
                    "top_products": top_products,
                    "category_sales": category_sales,
                    "low_stock_products": low_stock_products,
                    "top_customers": top_customers,
                    "executive_summary": executive_summary,
                },
            )
        finally:
            db.close()
