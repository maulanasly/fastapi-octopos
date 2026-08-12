from datetime import datetime, timedelta, timezone

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, ModelView, expose

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.core.database import SessionLocal
from app.core.localization import format_currency, get_localization_setting
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.localization import LocalizationSetting
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
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.stock_movement import StockMovement
from app.models.sync_event import SyncEventLog
from app.models.tax import OrderTaxLine, TaxRule
from app.models.user import User
from app.services.reports import (
    get_category_sales_data,
    get_executive_summary_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_top_customers_data,
    get_top_products_data,
)


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
        User.roles,
    ]
    column_searchable_list = [User.email, User.full_name]
    can_delete = False


class LocalizationSettingAdmin(ModelView, model=LocalizationSetting):
    column_list = [
        LocalizationSetting.id,
        LocalizationSetting.language,
        LocalizationSetting.timezone,
        LocalizationSetting.currency,
        LocalizationSetting.date_format,
        LocalizationSetting.number_format,
        LocalizationSetting.country_code,
        LocalizationSetting.updated_at,
    ]
    can_create = False
    can_delete = False


class RoleAdmin(ModelView, model=Role):
    column_list = [
        Role.id,
        Role.name,
        Role.description,
        Role.is_system,
        Role.permissions,
    ]
    column_searchable_list = [Role.name, Role.description]
    column_sortable_list = [Role.id, Role.name]


class PermissionAdmin(ModelView, model=Permission):
    column_list = [
        Permission.id,
        Permission.code,
        Permission.description,
        Permission.roles,
    ]
    column_searchable_list = [Permission.code, Permission.description]
    column_sortable_list = [Permission.id, Permission.code]


class UserRoleAdmin(ModelView, model=UserRole):
    column_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    column_sortable_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    can_create = False
    can_edit = False
    can_delete = False


class RolePermissionAdmin(ModelView, model=RolePermission):
    column_list = [
        RolePermission.id,
        RolePermission.role_id,
        RolePermission.permission_id,
    ]
    column_sortable_list = [
        RolePermission.id,
        RolePermission.role_id,
        RolePermission.permission_id,
    ]
    can_create = False
    can_edit = False
    can_delete = False


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.description]
    column_searchable_list = [Category.name]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.price,
        Product.unit_cost,
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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user,
        Order.customer,
        Order.promotion,
        Order.subtotal_amount,
        Order.discount_amount,
        Order.taxable_base_amount,
        Order.tax_total_amount,
        Order.grand_total_amount,
        Order.redeemed_points,
        Order.total_amount,
        Order.paid_amount,
        Order.change_amount,
        Order.remaining_amount,
        Order.status,
        Order.reservation_status,
        Order.reservation_expires_at,
        Order.created_at,
    ]
    column_sortable_list = [Order.created_at, Order.total_amount]
    column_searchable_list = [Order.id]
    can_create = False
    can_edit = False
    can_delete = False


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
    ]
    column_searchable_list = [OrderItem.order_id]
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


class TaxRuleAdmin(ModelView, model=TaxRule):
    column_list = [
        TaxRule.id,
        TaxRule.name,
        TaxRule.tax_scope,
        TaxRule.tax_mode,
        TaxRule.rate,
        TaxRule.product,
        TaxRule.category,
        TaxRule.starts_at,
        TaxRule.ends_at,
        TaxRule.is_active,
        TaxRule.updated_at,
    ]
    column_searchable_list = [TaxRule.name, TaxRule.description]
    column_sortable_list = [TaxRule.id, TaxRule.rate, TaxRule.updated_at]


class OrderTaxLineAdmin(ModelView, model=OrderTaxLine):
    column_list = [
        OrderTaxLine.id,
        OrderTaxLine.order_id,
        OrderTaxLine.tax_rule,
        OrderTaxLine.tax_name,
        OrderTaxLine.tax_scope,
        OrderTaxLine.tax_mode,
        OrderTaxLine.tax_rate,
        OrderTaxLine.taxable_base,
        OrderTaxLine.tax_amount,
        OrderTaxLine.applied_at,
    ]
    column_searchable_list = [OrderTaxLine.tax_name, OrderTaxLine.tax_scope]
    column_sortable_list = [OrderTaxLine.applied_at, OrderTaxLine.id]
    can_create = False
    can_edit = False
    can_delete = False


class ReportsAdmin(BaseView):
    name = "Reports Dashboard"
    icon = "fa-solid fa-chart-line"

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            localization = get_localization_setting(db)
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
            sales_summary = get_sales_summary_data(
                db=db, start_date=start_date, end_date=end_date
            )

            # 2. Top Selling Products
            top_products = get_top_products_data(
                db=db, start_date=start_date, end_date=end_date, limit=10
            )

            # 3. Sales by Category
            category_sales = get_category_sales_data(
                db=db, start_date=start_date, end_date=end_date
            )

            # 4. Low Stock Products (threshold <= 10)
            low_stock_products = get_low_stock_products_data(db=db, threshold=10)

            # 5. Top Customers
            top_customers = get_top_customers_data(
                db=db, start_date=start_date, end_date=end_date, limit=5
            )

            invoice_summary = get_invoice_summary_data(
                db=db, start_date=start_date, end_date=end_date
            )

            # 6. Executive Summary
            executive_summary = get_executive_summary_data(
                db=db, invoice_summary=invoice_summary
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
                "purchase_received_value": format_currency(
                    float(executive_summary["purchase_received_value"]),
                    localization.currency,
                    localization.number_format,
                ),
                "average_cash_variance": format_currency(
                    float(executive_summary["average_cash_variance"]),
                    localization.currency,
                    localization.number_format,
                ),
                "invoice_approved_total": format_currency(
                    float(executive_summary["invoice_approved_total"]),
                    localization.currency,
                    localization.number_format,
                ),
                "invoice_variance_total": format_currency(
                    float(executive_summary["invoice_variance_total"]),
                    localization.currency,
                    localization.number_format,
                ),
            }

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "period": period,
                    "period_label": period_labels[period],
                    "localization": localization,
                    "localized": localized,
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
