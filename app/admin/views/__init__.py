"""Admin views package — re-exports for backwards compatibility.

New code should import from the domain modules directly
(e.g. ``from app.admin.views.inventory import ProductAdmin``),
but ``from app.admin.views import ProductAdmin`` remains supported
via this shim.
"""

from app.admin.views.access import (
    PermissionAdmin,
    RoleAdmin,
    RolePermissionAdmin,
    UserAdmin,
    UserRoleAdmin,
)
from app.admin.views.inventory import CategoryAdmin, ProductAdmin, StockMovementAdmin
from app.admin.views.operations import DrawerSessionAdmin, ShiftReconciliationAdmin
from app.admin.views.purchasing import (
    PurchaseInvoiceAdmin,
    PurchaseInvoiceItemAdmin,
    PurchaseOrderAdmin,
    PurchaseOrderItemAdmin,
    SupplierAdmin,
    SupplierPaymentAdmin,
)
from app.admin.views.reports import ReportsAdmin
from app.admin.views.sales import (
    CustomerAdmin,
    LoyaltyTransactionAdmin,
    OrderAdmin,
    OrderItemAdmin,
    OrderTaxLineAdmin,
    PromotionAdmin,
    RefundAdmin,
    RefundItemAdmin,
    TaxRuleAdmin,
)
from app.admin.views.system import (
    LocalizationSettingAdmin,
    PurchasingSettingAdmin,
    SyncEventLogAdmin,
)
from app.admin.views.tenant import TenantAdmin, TenantSwitchAdmin
from app.admin.views.workflows import WorkflowsAdmin

__all__ = [
    "CategoryAdmin",
    "CustomerAdmin",
    "DrawerSessionAdmin",
    "LocalizationSettingAdmin",
    "LoyaltyTransactionAdmin",
    "OrderAdmin",
    "OrderItemAdmin",
    "OrderTaxLineAdmin",
    "PermissionAdmin",
    "ProductAdmin",
    "PromotionAdmin",
    "PurchaseInvoiceAdmin",
    "PurchaseInvoiceItemAdmin",
    "PurchaseOrderAdmin",
    "PurchaseOrderItemAdmin",
    "PurchasingSettingAdmin",
    "RefundAdmin",
    "RefundItemAdmin",
    "ReportsAdmin",
    "RoleAdmin",
    "RolePermissionAdmin",
    "ShiftReconciliationAdmin",
    "StockMovementAdmin",
    "SupplierAdmin",
    "SupplierPaymentAdmin",
    "SyncEventLogAdmin",
    "TaxRuleAdmin",
    "TenantAdmin",
    "TenantSwitchAdmin",
    "UserAdmin",
    "UserRoleAdmin",
    "WorkflowsAdmin",
]
