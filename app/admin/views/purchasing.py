# pyrefly: ignore [missing-import]
from sqladmin.filters import (
    AllUniqueStringValuesFilter,
    BooleanFilter,
    ForeignKeyFilter,
)
from starlette.requests import Request

from app.admin.base import TenantScopedModelView
from app.admin.formatting import LabeledRelationsMixin
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
)


class SupplierAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Supplier):
    name = "Suppliers"
    icon = "fa-solid fa-truck-field"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

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
    column_default_sort = [(Supplier.created_at, True)]
    column_filters = [BooleanFilter(Supplier.is_active, title="Active")]
    column_labels = {
        Supplier.name: "Supplier",
        Supplier.is_active: "Active",
        Supplier.contact_email: "Email",
    }
    column_descriptions = {
        Supplier.name: "Supplier display name, searchable",
        Supplier.is_active: "Inactive suppliers not offered in workflows",
    }
    form_args = {
        "name": {"render_kw": {"placeholder": "e.g. Acme Supplies"}},
        "contact_email": {"render_kw": {"placeholder": "contact@supplier.com"}},
    }


class PurchaseOrderAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseOrder
):
    name = "Purchase Orders"
    icon = "fa-solid fa-file-invoice"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

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
    column_default_sort = [(PurchaseOrder.created_at, True)]
    column_filters = [
        ForeignKeyFilter(
            PurchaseOrder.supplier_id, Supplier.name, foreign_model=Supplier
        ),
        AllUniqueStringValuesFilter(PurchaseOrder.status, title="Status"),
    ]
    column_labels = {PurchaseOrder.status: "Status", PurchaseOrder.supplier: "Supplier"}
    can_create = False
    can_edit = False
    can_delete = False


class PurchaseOrderItemAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseOrderItem
):
    name = "PO Items"
    icon = "fa-solid fa-list-check"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

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
    column_default_sort = [(PurchaseOrderItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False


class PurchaseInvoiceAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseInvoice
):
    name = "Purchase Invoices"
    icon = "fa-solid fa-file-invoice-dollar"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

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
    column_default_sort = [(PurchaseInvoice.created_at, True)]
    column_filters = [
        ForeignKeyFilter(
            PurchaseInvoice.supplier_id, Supplier.name, foreign_model=Supplier
        ),
        AllUniqueStringValuesFilter(PurchaseInvoice.status, title="Status"),
    ]
    column_labels = {
        PurchaseInvoice.invoice_number: "Invoice #",
        PurchaseInvoice.status: "Status",
        PurchaseInvoice.supplier: "Supplier",
    }
    can_create = False
    can_edit = False
    can_delete = False


class PurchaseInvoiceItemAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseInvoiceItem
):
    name = "Invoice Items"
    icon = "fa-solid fa-receipt"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

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
    column_default_sort = [(PurchaseInvoiceItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False

    def is_visible(self, request: Request) -> bool:
        return False


class SupplierPaymentAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=SupplierPayment
):
    name = "Supplier Payments"
    icon = "fa-solid fa-money-bill-transfer"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        SupplierPayment.id,
        SupplierPayment.supplier,
        SupplierPayment.invoice,
        SupplierPayment.user,
        SupplierPayment.amount,
        SupplierPayment.payment_method,
        SupplierPayment.status,
        SupplierPayment.payment_date,
        SupplierPayment.reference,
        SupplierPayment.created_at,
    ]
    column_searchable_list = [
        SupplierPayment.status,
        SupplierPayment.payment_method,
        SupplierPayment.reference,
    ]
    column_sortable_list = [
        SupplierPayment.created_at,
        SupplierPayment.amount,
        SupplierPayment.status,
    ]
    column_default_sort = [(SupplierPayment.created_at, True)]
    column_filters = [
        ForeignKeyFilter(
            SupplierPayment.supplier_id, Supplier.name, foreign_model=Supplier
        ),
        AllUniqueStringValuesFilter(SupplierPayment.status, title="Status"),
        AllUniqueStringValuesFilter(
            SupplierPayment.payment_method, title="Payment Method"
        ),
    ]
    column_labels = {
        SupplierPayment.status: "Status",
        SupplierPayment.supplier: "Supplier",
        SupplierPayment.payment_method: "Payment Method",
    }
    can_create = False
    can_edit = False
    can_delete = False
