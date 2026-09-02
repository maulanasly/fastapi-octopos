# pyrefly: ignore [missing-import]
from sqladmin.filters import (
    AllUniqueStringValuesFilter,
    ForeignKeyFilter,
    OperationColumnFilter,
)

from app.admin.base import TenantScopedModelView
from app.admin.formatting import LabeledRelationsMixin
from app.models.audit_log import AuditLog
from app.models.drawer import DrawerSession
from app.models.payment import Payment
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.user import User


class DrawerSessionAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=DrawerSession
):
    name = "Drawer Sessions"
    icon = "fa-solid fa-cash-register"
    category = "Operations"
    category_icon = "fa-solid fa-screwdriver-wrench"

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
        AllUniqueStringValuesFilter(DrawerSession.status, title="Status"),
        ForeignKeyFilter(DrawerSession.user_id, User.email, foreign_model=User),
        OperationColumnFilter(DrawerSession.opened_at, title="Opened"),
    ]
    column_searchable_list = [DrawerSession.status]
    column_sortable_list = [DrawerSession.opened_at, DrawerSession.closed_at]
    column_default_sort = [(DrawerSession.opened_at, True)]
    column_labels = {
        DrawerSession.user: "Cashier",
        DrawerSession.status: "Status",
        DrawerSession.opened_at: "Opened",
        DrawerSession.closed_at: "Closed",
        DrawerSession.starting_cash: "Starting Cash",
        DrawerSession.ending_cash: "Ending Cash",
    }
    column_descriptions = {
        DrawerSession.status: "open or closed — controls POS availability",
    }
    can_create = False
    can_edit = False
    can_delete = False


class ShiftReconciliationAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=ShiftReconciliation
):
    name = "Shift Reconciliations"
    icon = "fa-solid fa-calculator"
    category = "Operations"
    category_icon = "fa-solid fa-screwdriver-wrench"

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
    column_filters = [
        OperationColumnFilter(ShiftReconciliation.drawer_session_id, title="Drawer ID"),
        OperationColumnFilter(ShiftReconciliation.created_at, title="Created"),
    ]
    column_searchable_list = [ShiftReconciliation.drawer_session_id]
    column_sortable_list = [ShiftReconciliation.created_at, ShiftReconciliation.id]
    column_default_sort = [(ShiftReconciliation.created_at, True)]
    column_labels = {
        ShiftReconciliation.drawer_session_id: "Drawer Session",
        ShiftReconciliation.closed_by_user: "Closed By",
        ShiftReconciliation.expected_cash: "Expected Cash",
        ShiftReconciliation.counted_cash: "Counted Cash",
        ShiftReconciliation.cash_variance: "Cash Variance",
        ShiftReconciliation.expected_non_cash: "Expected Non-Cash",
        ShiftReconciliation.counted_non_cash: "Counted Non-Cash",
        ShiftReconciliation.non_cash_variance: "Non-Cash Variance",
        ShiftReconciliation.created_at: "Created",
    }
    column_descriptions = {
        ShiftReconciliation.cash_variance: "Difference between expected and counted cash",
    }
    can_create = False
    can_edit = False
    can_delete = False


class PaymentAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Payment):
    name = "Payments"
    icon = "fa-solid fa-credit-card"
    category = "Operations"
    category_icon = "fa-solid fa-screwdriver-wrench"

    column_list = [
        Payment.id,
        Payment.order_id,
        Payment.user,
        Payment.payment_method,
        Payment.amount,
        Payment.idempotency_key,
        Payment.created_at,
    ]
    column_searchable_list = [Payment.payment_method, Payment.idempotency_key]
    column_sortable_list = [Payment.created_at, Payment.amount, Payment.id]
    column_default_sort = [(Payment.created_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(Payment.payment_method, title="Method"),
        OperationColumnFilter(Payment.order_id, title="Order ID"),
        OperationColumnFilter(Payment.created_at, title="Created"),
        ForeignKeyFilter(Payment.user_id, User.email, foreign_model=User),
    ]
    column_labels = {
        Payment.order_id: "Order",
        Payment.user: "Cashier",
        Payment.payment_method: "Method",
        Payment.amount: "Amount",
        Payment.idempotency_key: "Idempotency Key",
        Payment.created_at: "Created",
    }
    column_descriptions = {
        Payment.payment_method: "Cash, card, mobile, etc.",
        Payment.amount: "Payment amount in store currency",
    }
    can_create = False
    can_edit = False
    can_delete = False


class AuditLogAdmin(LabeledRelationsMixin, TenantScopedModelView, model=AuditLog):
    name = "Audit Log"
    icon = "fa-solid fa-clipboard-list"
    category = "System"
    category_icon = "fa-solid fa-gear"

    # AuditLog.tenant_id nullable (platform actions), keep tenant filter dropdown
    # but show all rows — TenantScopedModelView injects the tenant column/filter.

    column_list = [
        AuditLog.id,
        AuditLog.user,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.ip_address,
        AuditLog.created_at,
    ]
    column_details_list = [
        AuditLog.id,
        AuditLog.tenant_id,
        AuditLog.user,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.details_json,
        AuditLog.ip_address,
        AuditLog.request_id,
        AuditLog.created_at,
    ]
    column_searchable_list = [AuditLog.action, AuditLog.resource_type]
    column_sortable_list = [AuditLog.created_at, AuditLog.id]
    column_default_sort = [(AuditLog.created_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(AuditLog.action, title="Action"),
        AllUniqueStringValuesFilter(AuditLog.resource_type, title="Resource"),
        OperationColumnFilter(AuditLog.created_at, title="Created"),
        OperationColumnFilter(AuditLog.resource_id, title="Resource ID"),
    ]
    column_labels = {
        AuditLog.user: "Actor",
        AuditLog.action: "Action",
        AuditLog.resource_type: "Resource",
        AuditLog.resource_id: "Resource ID",
        AuditLog.details_json: "Details",
        AuditLog.ip_address: "IP",
        AuditLog.request_id: "Request ID",
        AuditLog.created_at: "Created",
    }
    column_descriptions = {
        AuditLog.action: "e.g. admin.stock_adjust, orders.create",
    }
    can_create = False
    can_edit = False
    can_delete = False
