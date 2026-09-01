from datetime import datetime

from pydantic import BaseModel, Field


class StockMovement(BaseModel):
    id: int
    product_id: int
    user_id: int | None = None
    order_id: int | None = None
    order_item_id: int | None = None
    purchase_order_id: int | None = None
    purchase_order_item_id: int | None = None
    refund_id: int | None = None
    movement_type: str
    quantity_before: int
    quantity_delta: int
    quantity_after: int
    note: str | None = None
    created_at: datetime
    # Enriched fields for intuitive UI
    product_name: str | None = None
    product_sku: str | None = None
    user_email: str | None = None

    model_config = {"from_attributes": True}


class InventoryReceiptCreate(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., gt=0, description="Quantity to add (positive)")
    unit_cost: float | None = Field(None, ge=0, description="Optional new unit cost")
    supplier_id: int | None = Field(None, ge=1)
    note: str | None = Field(None, max_length=255)
