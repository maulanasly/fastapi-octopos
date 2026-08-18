from datetime import datetime

from pydantic import BaseModel, Field


class SupplierBase(BaseModel):
    name: str
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool | None = None


class Supplier(SupplierBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity_ordered: int = Field(ge=1)
    unit_cost: float = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    notes: str | None = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderReceiveItem(BaseModel):
    purchase_order_item_id: int
    quantity_received: int = Field(ge=1)


class PurchaseOrderReceive(BaseModel):
    items: list[PurchaseOrderReceiveItem]


class PurchaseOrderItem(BaseModel):
    id: int
    purchase_order_id: int
    product_id: int
    quantity_ordered: int
    quantity_received: int
    unit_cost: float

    model_config = {"from_attributes": True}


class PurchaseOrder(BaseModel):
    id: int
    supplier_id: int
    user_id: int
    status: str
    total_estimated_amount: float
    notes: str | None = None
    created_at: datetime
    ordered_at: datetime | None = None
    received_at: datetime | None = None
    items: list[PurchaseOrderItem] = []

    model_config = {"from_attributes": True}


class PurchaseInvoiceItemCreate(BaseModel):
    purchase_order_item_id: int
    billed_quantity: int = Field(ge=1)
    billed_unit_cost: float = Field(ge=0)


class PurchaseInvoiceCreate(BaseModel):
    purchase_order_id: int
    invoice_number: str
    invoice_date: datetime | None = None
    due_date: datetime | None = None
    notes: str | None = None
    items: list[PurchaseInvoiceItemCreate]


class PurchaseInvoiceReviewAction(BaseModel):
    review_note: str | None = None


class PurchaseInvoiceItem(BaseModel):
    id: int
    invoice_id: int
    purchase_order_item_id: int
    product_id: int
    billed_quantity: int
    billed_unit_cost: float
    expected_quantity: int
    expected_unit_cost: float
    quantity_variance: int
    price_variance: float
    line_total: float

    model_config = {"from_attributes": True}


class PurchaseInvoice(BaseModel):
    id: int
    supplier_id: int
    purchase_order_id: int
    user_id: int
    invoice_number: str
    status: str
    invoice_date: datetime | None = None
    due_date: datetime | None = None
    subtotal_amount: float
    total_amount: float
    variance_amount: float
    has_quantity_variance: bool
    has_price_variance: bool
    notes: str | None = None
    review_note: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime
    items: list[PurchaseInvoiceItem] = []

    model_config = {"from_attributes": True}


class PurchaseInvoiceSummary(BaseModel):
    invoice_count: int
    approved_count: int
    rejected_count: int
    pending_review_count: int
    draft_count: int
    approved_total: float
    billed_total: float
    variance_total: float
