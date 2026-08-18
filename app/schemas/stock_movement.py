from datetime import datetime

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}
