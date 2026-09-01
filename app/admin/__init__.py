"""Admin views module — aggregator keeps sqladmin registration stable."""

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

all_admin_views = [
    WorkflowsAdmin,
    OrderAdmin,
    OrderItemAdmin,
    OrderTaxLineAdmin,
    RefundAdmin,
    RefundItemAdmin,
    CustomerAdmin,
    LoyaltyTransactionAdmin,
    SupplierAdmin,
    PurchaseOrderAdmin,
    PurchaseOrderItemAdmin,
    PurchaseInvoiceAdmin,
    PurchaseInvoiceItemAdmin,
    SupplierPaymentAdmin,
    ProductAdmin,
    CategoryAdmin,
    StockMovementAdmin,
    PromotionAdmin,
    TaxRuleAdmin,
    DrawerSessionAdmin,
    ShiftReconciliationAdmin,
    UserAdmin,
    RoleAdmin,
    PermissionAdmin,
    UserRoleAdmin,
    RolePermissionAdmin,
    LocalizationSettingAdmin,
    PurchasingSettingAdmin,
    SyncEventLogAdmin,
    ReportsAdmin,
    TenantSwitchAdmin,
    TenantAdmin,
]
