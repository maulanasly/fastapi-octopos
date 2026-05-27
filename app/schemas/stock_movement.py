from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StockMovement(BaseModel):
    id: int
    product_id: int
    user_id: Optional[int] = None
    order_id: Optional[int] = None
    order_item_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    purchase_order_item_id: Optional[int] = None
    refund_id: Optional[int] = None
    movement_type: str
    quantity_before: int
    quantity_delta: int
    quantity_after: int
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
