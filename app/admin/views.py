from datetime import datetime, timedelta, timezone

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, Flash, ModelView, action, expose
from sqladmin.filters import AllUniqueStringValuesFilter, ForeignKeyFilter
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException
# pyrefly: ignore [missing-import]
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.admin.formatting import LabeledRelationsMixin
from app.core.audit import log_action
from app.core.database import SessionLocal
from app.core.localization import format_currency, get_localization_setting
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.localization import LocalizationSetting
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.purchase import (PurchaseInvoice, PurchaseInvoiceItem,
                                 PurchaseOrder, PurchaseOrderItem, Supplier)
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.stock_movement import StockMovement
from app.models.sync_event import SyncEventLog
from app.models.tax import OrderTaxLine, TaxRule
from app.models.user import User
from app.services.reports import (get_category_sales_data,
                                  get_executive_summary_data,
                                  get_invoice_summary_data,
                                  get_low_stock_products_data,
                                  get_sales_summary_data,
                                  get_top_customers_data,
                                  get_top_products_data)

REPORTS_CACHE_SECONDS = 120
_reports_cache: dict[tuple[str, str, str], tuple[float, dict]] = {}


class UserAdmin(LabeledRelationsMixin, ModelView, model=User):
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


class LocalizationSettingAdmin(
    LabeledRelationsMixin, ModelView, model=LocalizationSetting
):
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


class RoleAdmin(LabeledRelationsMixin, ModelView, model=Role):
    column_list = [
        Role.id,
        Role.name,
        Role.description,
        Role.is_system,
        Role.permissions,
    ]
    # To-many relationships are only rendered in the detail view (sqladmin
    # list view skips them); explicit column_details_list keeps the mixin's
    # formatters active so codes render instead of object reprs.
    column_details_list = [
        Role.id,
        Role.name,
        Role.description,
        Role.is_system,
        Role.permissions,
    ]
    column_searchable_list = [Role.name, Role.description]
    column_sortable_list = [Role.id, Role.name]

    async def check_can_edit(self, request: Request, model: Role) -> bool:
        if getattr(model, "is_system", False):
            return False
        return True

    async def check_can_delete(self, request: Request, model: Role) -> bool:
        if getattr(model, "is_system", False):
            return False
        return True


class PermissionAdmin(LabeledRelationsMixin, ModelView, model=Permission):
    column_list = [
        Permission.id,
        Permission.code,
        Permission.description,
        Permission.roles,
    ]
    column_searchable_list = [Permission.code, Permission.description]
    column_sortable_list = [Permission.id, Permission.code]


class UserRoleAdmin(LabeledRelationsMixin, ModelView, model=UserRole):
    column_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    column_sortable_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    can_create = False
    can_edit = False
    can_delete = False


class RolePermissionAdmin(LabeledRelationsMixin, ModelView, model=RolePermission):
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


class CategoryAdmin(LabeledRelationsMixin, ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.description]
    column_searchable_list = [Category.name]


class ProductAdmin(LabeledRelationsMixin, ModelView, model=Product):
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

    # Stock is ledger-managed via the stock-adjustment action below; never
    # edit it directly through the create/edit forms.
    form_excluded_columns = [Product.stock_quantity]

    @action(
        "adjust-stock",
        label="Record Stock Adjustment",
        confirmation_message=(
            "A StockMovement ledger entry will be recorded. Continue?"
        ),
    )
    async def adjust_stock_action(self, request: Request):
        pk = request.query_params.get("pks", "").split(",")[0]
        return RedirectResponse(
            url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
        )

    @expose("/adjust-stock", methods=["GET", "POST"])
    async def adjust_stock_page(self, request: Request):
        pk = request.query_params.get("pk")
        if not pk:
            raise HTTPException(status_code=404)
        db = self.session_maker()
        try:
            product = db.get(Product, int(pk))
            if not product:
                raise HTTPException(status_code=404)

            if request.method == "POST":
                form = await request.form()
                try:
                    delta = int(form.get("delta"))
                except (TypeError, ValueError):
                    Flash.error(
                        request, "Delta must be a whole number.", "Invalid input"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                note = (form.get("note") or "").strip()
                if delta == 0:
                    Flash.warning(request, "Delta of zero records no movement.")
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                quantity_before = product.stock_quantity or 0
                quantity_after = quantity_before + delta
                if quantity_after < 0:
                    Flash.error(
                        request, "Stock cannot go below zero.", "Insufficient stock"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                product.stock_quantity = quantity_after
                db.add(
                    StockMovement(
                        product_id=product.id,
                        user_id=request.session.get("admin_user_id"),
                        movement_type="manual_adjustment",
                        quantity_before=quantity_before,
                        quantity_delta=delta,
                        quantity_after=quantity_after,
                        note=note or "Manual stock adjustment from admin",
                    )
                )
                log_action(
                    db=db,
                    action="admin.stock_adjust",
                    user_id=request.session.get("admin_user_id"),
                    resource_type="product",
                    resource_id=product.id,
                    details={
                        "quantity_before": quantity_before,
                        "quantity_after": quantity_after,
                        "delta": delta,
                        "note": note,
                    },
                )
                db.commit()
                Flash.success(
                    request,
                    f"Stock adjusted from {quantity_before} to {quantity_after}.",
                )
                return RedirectResponse(
                    url=f"/admin/product/details/{product.id}", status_code=303
                )

            return await self.templates.TemplateResponse(
                request,
                "product_adjust_stock.html",
                context={
                    "product": product,
                    "title": f"Adjust Stock: {product.name}",
                },
            )
        finally:
            db.close()


class PromotionAdmin(LabeledRelationsMixin, ModelView, model=Promotion):
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


class CustomerAdmin(LabeledRelationsMixin, ModelView, model=Customer):
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


class LoyaltyTransactionAdmin(
    LabeledRelationsMixin, ModelView, model=LoyaltyTransaction
):
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


class SupplierAdmin(LabeledRelationsMixin, ModelView, model=Supplier):
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


class PurchaseOrderAdmin(LabeledRelationsMixin, ModelView, model=PurchaseOrder):
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


class PurchaseOrderItemAdmin(LabeledRelationsMixin, ModelView, model=PurchaseOrderItem):
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


class PurchaseInvoiceAdmin(LabeledRelationsMixin, ModelView, model=PurchaseInvoice):
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


class PurchaseInvoiceItemAdmin(
    LabeledRelationsMixin, ModelView, model=PurchaseInvoiceItem
):
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


class OrderAdmin(LabeledRelationsMixin, ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user,
        Order.customer,
        Order.status,
        Order.promotion,
        Order.grand_total_amount,
        Order.paid_amount,
        Order.remaining_amount,
        Order.created_at,
    ]
    column_details_list = [
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


class OrderItemAdmin(LabeledRelationsMixin, ModelView, model=OrderItem):
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


class DrawerSessionAdmin(LabeledRelationsMixin, ModelView, model=DrawerSession):
    column_list = [
        DrawerSession.id,
        DrawerSession.user,
        DrawerSession.opened_at,
        DrawerSession.closed_at,
        DrawerSession.starting_cash,
        DrawerSession.ending_cash,
        DrawerSession.status,
    ]
    column_filters = [
        AllUniqueStringValuesFilter(DrawerSession.status),
        ForeignKeyFilter(DrawerSession.user_id, User.email, foreign_model=User),
    ]
    column_searchable_list = [DrawerSession.status]
    column_sortable_list = [DrawerSession.opened_at, DrawerSession.closed_at]
    can_create = False
    can_edit = False
    can_delete = False


class ShiftReconciliationAdmin(
    LabeledRelationsMixin, ModelView, model=ShiftReconciliation
):
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


class RefundAdmin(LabeledRelationsMixin, ModelView, model=Refund):
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


class RefundItemAdmin(LabeledRelationsMixin, ModelView, model=RefundItem):
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


class StockMovementAdmin(LabeledRelationsMixin, ModelView, model=StockMovement):
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


class SyncEventLogAdmin(LabeledRelationsMixin, ModelView, model=SyncEventLog):
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


class TaxRuleAdmin(LabeledRelationsMixin, ModelView, model=TaxRule):
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


class OrderTaxLineAdmin(LabeledRelationsMixin, ModelView, model=OrderTaxLine):
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

    def _period_range(self, now: datetime, period: str) -> tuple:
        if period == "today":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=timezone.utc,
            )
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "month":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=1,
                tzinfo=timezone.utc,
            )
        else:
            start_date = None
        return start_date, None

    def _build_report_data(self, db, period: str, localization) -> dict:
        now = datetime.now(timezone.utc)
        if period not in ("today", "7d", "30d", "month"):
            period = "all"
        start_date, end_date = self._period_range(now, period)

        sales_summary = get_sales_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        top_products = get_top_products_data(
            db=db, start_date=start_date, end_date=end_date, limit=10
        )
        category_sales = get_category_sales_data(
            db=db, start_date=start_date, end_date=end_date
        )
        low_stock_products = get_low_stock_products_data(db=db)
        top_customers = get_top_customers_data(
            db=db, start_date=start_date, end_date=end_date, limit=5
        )
        invoice_summary = get_invoice_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
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

        top_products_view = [
            {
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in top_products
        ]
        category_sales_view = [
            {
                "category_name": row.category_name,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in category_sales
        ]
        top_customers_view = [
            {
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "order_count": row.order_count,
                "total_spent": row.total_spent,
                "total_spent_formatted": format_currency(
                    float(row.total_spent or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
                "points_balance": row.points_balance,
            }
            for row in top_customers
        ]

        return {
            "period_label": {
                "today": "Today",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "month": "This Month",
                "all": "All Time",
            }[period],
            "localized": localized,
            "sales_summary": sales_summary,
            "top_products": top_products_view,
            "category_sales": category_sales_view,
            "low_stock_products": low_stock_products,
            "top_customers": top_customers_view,
            "executive_summary": executive_summary,
        }

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            localization = get_localization_setting(db)
            period = request.query_params.get("period", "30d")

            shift_reports = (
                db.query(ShiftReconciliation)
                .options(
                    joinedload(ShiftReconciliation.drawer_session),
                    joinedload(ShiftReconciliation.closed_by_user),
                )
                .order_by(ShiftReconciliation.id.desc())
                .limit(10)
                .all()
            )

            cache_key = (period, localization.currency, localization.number_format)
            cached = _reports_cache.get(cache_key)
            now = datetime.now(timezone.utc).timestamp()
            if cached and now - cached[0] < REPORTS_CACHE_SECONDS:
                data = cached[1]
            else:
                data = self._build_report_data(db, period, localization)
                _reports_cache[cache_key] = (
                    now,
                    {
                        k: (v.copy() if isinstance(v, dict) else v)
                        for k, v in data.items()
                    },
                )

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "period": period,
                    "period_label": data["period_label"],
                    "localization": localization,
                    "localized": data["localized"],
                    "sales_summary": data["sales_summary"],
                    "top_products": data["top_products"],
                    "category_sales": data["category_sales"],
                    "low_stock_products": data["low_stock_products"],
                    "top_customers": data["top_customers"],
                    "executive_summary": data["executive_summary"],
                    "shift_reports": shift_reports,
                },
            )
        finally:
            db.close()

    @expose("/reports/shift/{reconciliation_id}/print", methods=["GET"])
    async def shift_report_print_page(self, request: Request, reconciliation_id: int):
        """Print-friendly Z-report for a closed drawer shift (admin session)."""
        from datetime import datetime as _dt

        from app.services.reports import get_shift_report_data

        db = SessionLocal()
        try:
            data = get_shift_report_data(db=db, reconciliation_id=reconciliation_id)
            if data is None:
                raise HTTPException(status_code=404)
            rec = data["reconciliation"]
            drawer = data["drawer"]
            report = {
                "reconciliation_id": rec.id,
                "drawer_session_id": rec.drawer_session_id,
                "opened_at": drawer.opened_at if drawer else None,
                "closed_at": drawer.closed_at if drawer else None,
                "operator_name": data["operator_name"],
                "closed_by_name": data["closed_by_name"],
                "starting_cash": float(drawer.starting_cash or 0.0) if drawer else 0.0,
                "expected_cash": float(rec.expected_cash or 0.0),
                "counted_cash": float(rec.counted_cash or 0.0),
                "cash_variance": float(rec.cash_variance or 0.0),
                "expected_non_cash": float(rec.expected_non_cash or 0.0),
                "counted_non_cash": float(rec.counted_non_cash or 0.0),
                "non_cash_variance": float(rec.non_cash_variance or 0.0),
                "cash_sales_total": float(rec.cash_sales_total or 0.0),
                "non_cash_sales_total": float(rec.non_cash_sales_total or 0.0),
                "refunds_total": float(rec.refunds_total or 0.0),
                "gross_sales_total": float(rec.gross_sales_total or 0.0),
                "net_sales_total": float(rec.net_sales_total or 0.0),
                "completed_order_count": int(rec.completed_order_count or 0),
                "payment_breakdown": data["payment_breakdown"],
            }
            return await self.templates.TemplateResponse(
                request,
                "report_shift.html",
                context={
                    "report": report,
                    "now": _dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "title": f"Shift Report #{rec.id}",
                },
            )
        finally:
            db.close()
