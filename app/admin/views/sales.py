# pyrefly: ignore [missing-import]
from sqladmin import ModelView  # noqa: F401
from sqladmin.filters import (
    AllUniqueStringValuesFilter,
    BooleanFilter,
    OperationColumnFilter,
)

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.base import TenantScopedModelView
from app.admin.formatting import LabeledRelationsMixin
from app.models.customer import Customer, LoyaltyTransaction
from app.models.order import Order, OrderItem
from app.models.promotion import Promotion
from app.models.refund import Refund, RefundItem
from app.models.tax import OrderTaxLine, TaxRule


class PromotionAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Promotion):
    name = "Promotions"
    icon = "fa-solid fa-tags"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(Promotion.created_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(Promotion.discount_type, title="Discount Type"),
        BooleanFilter(Promotion.is_active, title="Active"),
    ]
    column_labels = {
        Promotion.code: "Promo Code",
        Promotion.name: "Promotion",
        Promotion.is_active: "Active",
        Promotion.discount_type: "Type",
        Promotion.discount_value: "Value",
        Promotion.applies_to: "Applies To",
    }
    column_descriptions = {
        Promotion.code: "Code customers enter at checkout",
        Promotion.discount_type: "percentage or fixed amount",
        Promotion.discount_value: "e.g. 10 for 10% or 5000 for fixed",
        Promotion.applies_to: "order or specific product scope",
        Promotion.is_active: "Inactive promos hidden at POS",
    }
    form_args = {
        "code": {"render_kw": {"placeholder": "e.g. WELCOME10"}},
        "discount_value": {"render_kw": {"placeholder": "10"}},
    }


class TaxRuleAdmin(LabeledRelationsMixin, TenantScopedModelView, model=TaxRule):
    name = "Tax Rules"
    icon = "fa-solid fa-percent"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(TaxRule.updated_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(TaxRule.tax_scope, title="Scope"),
        AllUniqueStringValuesFilter(TaxRule.tax_mode, title="Mode"),
        BooleanFilter(TaxRule.is_active, title="Active"),
    ]
    column_labels = {
        TaxRule.name: "Tax Rule",
        TaxRule.is_active: "Active",
        TaxRule.tax_scope: "Scope",
        TaxRule.tax_mode: "Mode",
        TaxRule.rate: "Rate",
    }
    column_descriptions = {
        TaxRule.rate: "0.10 = 10%  (e.g. 0.07 for 7%)",
        TaxRule.tax_scope: "order-wide or per-product",
        TaxRule.tax_mode: "exclusive (added) vs inclusive (included)",
        TaxRule.is_active: "Inactive rules not applied at checkout",
    }
    form_args = {
        "rate": {"render_kw": {"placeholder": "0.10"}},
        "name": {"render_kw": {"placeholder": "e.g. VAT 10%"}},
    }


class CustomerAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Customer):
    name = "Customers"
    icon = "fa-solid fa-user-group"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(Customer.created_at, True)]
    column_filters = [BooleanFilter(Customer.is_active, title="Active")]
    column_labels = {
        Customer.name: "Customer",
        Customer.is_active: "Active",
        Customer.email: "Email",
        Customer.points_balance: "Points",
    }
    column_descriptions = {Customer.name: "Full name, searchable with email/phone"}


class LoyaltyTransactionAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=LoyaltyTransaction
):
    name = "Loyalty Transactions"
    icon = "fa-solid fa-star"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(LoyaltyTransaction.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False


class OrderAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Order):
    name = "Sales Orders"
    icon = "fa-solid fa-cart-shopping"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(Order.created_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(Order.status, title="Status"),
        # Huge customer list: ID input avoids loading 10k customers
        OperationColumnFilter(Order.customer_id, title="Customer ID"),
        OperationColumnFilter(Order.created_at, title="Created"),
    ]
    column_labels = {
        Order.id: "Order #",
        Order.status: "Status",
        Order.customer: "Customer",
        Order.user: "Cashier",
        Order.grand_total_amount: "Total",
        Order.paid_amount: "Paid",
        Order.remaining_amount: "Due",
        Order.created_at: "Created",
    }
    column_descriptions = {
        Order.status: "Order lifecycle: pending → serving → completed/cancelled",
        Order.grand_total_amount: "Total after discounts and taxes",
    }
    can_create = False
    can_edit = False
    can_delete = False


class OrderItemAdmin(LabeledRelationsMixin, TenantScopedModelView, model=OrderItem):
    name = "Order Items"
    icon = "fa-solid fa-basket-shopping"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
    ]
    column_searchable_list = [OrderItem.order_id]
    column_default_sort = [(OrderItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False


class OrderTaxLineAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=OrderTaxLine
):
    name = "Order Tax Lines"
    icon = "fa-solid fa-receipt"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

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
    column_default_sort = [(OrderTaxLine.applied_at, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False


class RefundAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Refund):
    name = "Sales Refunds"
    icon = "fa-solid fa-rotate-left"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        Refund.id,
        Refund.order_id,
        Refund.user,
        Refund.total_amount,
        Refund.created_at,
    ]
    column_searchable_list = [Refund.order_id]
    column_sortable_list = [Refund.created_at, Refund.total_amount]
    column_default_sort = [(Refund.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class RefundItemAdmin(LabeledRelationsMixin, TenantScopedModelView, model=RefundItem):
    name = "Refund Items"
    icon = "fa-solid fa-rotate"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        RefundItem.id,
        RefundItem.refund_id,
        RefundItem.order_item_id,
        RefundItem.product,
        RefundItem.quantity,
        RefundItem.unit_price,
    ]
    column_searchable_list = [RefundItem.refund_id, RefundItem.order_item_id]
    column_default_sort = [(RefundItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False
