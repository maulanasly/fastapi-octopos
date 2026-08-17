from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from app.schemas.customer import Customer
from app.schemas.payment import Payment
from app.schemas.product import Product
from app.schemas.tax import OrderTaxLine
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
    idempotency_key: Optional[str] = None
    redeem_points: int = Field(0, ge=0)


class Order(OrderBase):
    id: int
    user_id: int
    customer_id: Optional[int] = None
    promotion_id: Optional[int] = None
    drawer_session_id: Optional[int] = None
    idempotency_key: Optional[str] = None
    subtotal_amount: Optional[float] = None
    discount_amount: float
    taxable_base_amount: float
    tax_total_amount: float
    grand_total_amount: float
    total_amount: float
    paid_amount: float
    change_amount: float
    remaining_amount: float
    redeemed_points: int
    status: str
    serving_status: str
    preparing_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
    reservation_status: str
    reservation_expires_at: Optional[datetime] = None
    created_at: datetime
    items: List[OrderItem] = []
    payments: List[Payment] = []
    tax_lines: List[OrderTaxLine] = []
    user: Optional[User] = None
    customer: Optional[Customer] = None

    model_config = {"from_attributes": True}


class ReservationReleaseSummary(BaseModel):
    released_count: int
    skipped_paid_count: int
    released_order_ids: List[int]
    skipped_paid_order_ids: List[int]


class ReceiptOrderItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float


class OrderReceipt(BaseModel):
    order_id: int
    created_at: datetime
    customer_name: Optional[str] = None
    cashier_name: Optional[str] = None
    subtotal_amount: float
    discount_amount: float
    redeemed_points: int
    taxable_base_amount: float
    tax_total_amount: float
    grand_total_amount: float
    total_amount: float
    paid_amount: float
    change_amount: float
    remaining_amount: float
    status: str
    serving_status: str
    reservation_status: str
    items: List[ReceiptOrderItem]
    tax_lines: List[OrderTaxLine]
    payments: List[Payment]
