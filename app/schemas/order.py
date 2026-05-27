from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from app.schemas.customer import Customer
from app.schemas.payment import Payment
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
    customer_id: Optional[int] = None
    promotion_code: Optional[str] = None
    redeem_points: int = Field(0, ge=0)


class Order(OrderBase):
    id: int
    user_id: int
    customer_id: Optional[int] = None
    promotion_id: Optional[int] = None
    drawer_session_id: Optional[int] = None
    subtotal_amount: Optional[float] = None
    discount_amount: float
    total_amount: float
    redeemed_points: int
    status: str
    created_at: datetime
    items: List[OrderItem] = []
    payments: List[Payment] = []
    user: Optional[User] = None
    customer: Optional[Customer] = None

    model_config = {"from_attributes": True}
