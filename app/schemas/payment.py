from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentBase(BaseModel):
    payment_method: str
    amount: float


class PaymentCreate(PaymentBase):
    idempotency_key: Optional[str] = None


class Payment(PaymentBase):
    id: int
    order_id: int
    user_id: int
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
