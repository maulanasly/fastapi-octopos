from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SupplierBase(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


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
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderReceiveItem(BaseModel):
    purchase_order_item_id: int
    quantity_received: int = Field(ge=1)


class PurchaseOrderReceive(BaseModel):
    items: List[PurchaseOrderReceiveItem]


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
    notes: Optional[str] = None
    created_at: datetime
    ordered_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    items: List[PurchaseOrderItem] = []

    model_config = {"from_attributes": True}


class PurchaseInvoiceItemCreate(BaseModel):
    purchase_order_item_id: int
    billed_quantity: int = Field(ge=1)
    billed_unit_cost: float = Field(ge=0)


class PurchaseInvoiceCreate(BaseModel):
    purchase_order_id: int
    invoice_number: str
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[PurchaseInvoiceItemCreate]


class PurchaseInvoiceReviewAction(BaseModel):
    review_note: Optional[str] = None


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
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    subtotal_amount: float
    total_amount: float
    variance_amount: float
    has_quantity_variance: bool
    has_price_variance: bool
    notes: Optional[str] = None
    review_note: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    items: List[PurchaseInvoiceItem] = []

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
