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
