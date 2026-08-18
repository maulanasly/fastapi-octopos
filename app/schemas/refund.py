from datetime import datetime

from pydantic import BaseModel, Field


class RefundItemCreate(BaseModel):
    order_item_id: int
    quantity: int = Field(ge=1)


class RefundCreate(BaseModel):
    order_id: int
    reason: str | None = None
    idempotency_key: str | None = None
    payment_method: str | None = None
    items: list[RefundItemCreate]


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
    reason: str | None = None
    idempotency_key: str | None = None
    payment_method: str | None = None
    total_amount: float
    created_at: datetime
    items: list[RefundItem] = []

    model_config = {"from_attributes": True}
