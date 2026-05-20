from datetime import datetime

from pydantic import BaseModel


class PaymentBase(BaseModel):
    payment_method: str
    amount: float


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    id: int
    order_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
