from datetime import datetime

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
    product: Product | None = None

    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    pass


class OrderCreate(OrderBase):
    items: list[OrderItemCreate]
    customer_id: int | None = None
    promotion_code: str | None = None
    idempotency_key: str | None = None
    redeem_points: int = Field(0, ge=0)
    destination_address: str | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None


class LocationUpdate(BaseModel):
    lat: float
    lng: float
    source: str = "gps"
    created_at: datetime


class Order(OrderBase):
    id: int
    user_id: int
    customer_id: int | None = None
    promotion_id: int | None = None
    drawer_session_id: int | None = None
    idempotency_key: str | None = None
    subtotal_amount: float | None = None
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
    preparing_at: datetime | None = None
    ready_at: datetime | None = None
    served_at: datetime | None = None
    reservation_status: str
    reservation_expires_at: datetime | None = None
    destination_address: str | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None
    tracking_status: str = "none"
    assigned_at: datetime | None = None
    en_route_at: datetime | None = None
    on_site_at: datetime | None = None
    latest_location: LocationUpdate | None = None
    created_at: datetime
    items: list[OrderItem] = []
    payments: list[Payment] = []
    tax_lines: list[OrderTaxLine] = []
    user: User | None = None
    customer: Customer | None = None

    model_config = {"from_attributes": True}


class ReservationReleaseSummary(BaseModel):
    released_count: int
    skipped_paid_count: int
    released_order_ids: list[int]
    skipped_paid_order_ids: list[int]


class ReceiptOrderItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float


class OrderReceipt(BaseModel):
    order_id: int
    created_at: datetime
    customer_name: str | None = None
    cashier_name: str | None = None
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
    items: list[ReceiptOrderItem]
    tax_lines: list[OrderTaxLine]
    payments: list[Payment]
