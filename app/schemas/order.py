from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.product import Product
from app.schemas.user import User


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    unit_price: float
    product: Optional[Product] = None

    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    pass


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItem] = []
    user: Optional[User] = None

    model_config = {"from_attributes": True}
