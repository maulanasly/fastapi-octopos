"""Admin views module — aggregator keeps sqladmin registration stable."""

from app.admin.views.access import (
    PermissionAdmin,
    RoleAdmin,
    RolePermissionAdmin,
    UserAdmin,
    UserRoleAdmin,
)
from app.admin.views.inventory import CategoryAdmin, ProductAdmin, StockMovementAdmin
from app.admin.views.operations import (
    AuditLogAdmin,
    DrawerSessionAdmin,
    PaymentAdmin,
    ShiftReconciliationAdmin,
)
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
    # Platform — tenant context first (scopes all writes)
    TenantSwitchAdmin,
    TenantAdmin,
    # Workflows — guided daily tasks
    WorkflowsAdmin,
    # Sales — Orders, Customers, Marketing (merged for daily ops)
    OrderAdmin,
    RefundAdmin,
    CustomerAdmin,
    PromotionAdmin,
    TaxRuleAdmin,
    # Inventory — catalog + ledger
    ProductAdmin,
    CategoryAdmin,
    StockMovementAdmin,
    # Purchasing — suppliers & documents
    SupplierAdmin,
    PurchaseOrderAdmin,
    PurchaseInvoiceAdmin,
    SupplierPaymentAdmin,
    # Operations — cash & shifts & payments
    DrawerSessionAdmin,
    ShiftReconciliationAdmin,
    PaymentAdmin,
    # Reports — KPIs
    ReportsAdmin,
    # Administration — tenant-scoped settings & RBAC
    UserAdmin,
    RoleAdmin,
    LocalizationSettingAdmin,
    PurchasingSettingAdmin,
    AuditLogAdmin,
    # Hidden detail/audit — kept for detail routes, not in menu
    OrderItemAdmin,
    OrderTaxLineAdmin,
    RefundItemAdmin,
    LoyaltyTransactionAdmin,
    PurchaseOrderItemAdmin,
    PurchaseInvoiceItemAdmin,
    PermissionAdmin,
    UserRoleAdmin,
    RolePermissionAdmin,
    SyncEventLogAdmin,
]
