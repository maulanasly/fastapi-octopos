from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RefundItemCreate(BaseModel):
    order_item_id: int
    quantity: int = Field(ge=1)


class RefundCreate(BaseModel):
    order_id: int
    reason: Optional[str] = None
    items: List[RefundItemCreate]


class RefundItem(BaseModel):
    id: int
    refund_id: int
    order_item_id: int
    product_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class Refund(BaseModel):
    id: int
    order_id: int
    user_id: int
    reason: Optional[str] = None
    total_amount: float
    created_at: datetime
    items: List[RefundItem] = []

    model_config = {"from_attributes": True}
