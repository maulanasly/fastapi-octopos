from datetime import datetime

from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    payment_method: str
    amount: float = Field(gt=0)


class PaymentCreate(PaymentBase):
    idempotency_key: str | None = None


class Payment(PaymentBase):
    id: int
    order_id: int
    user_id: int
    idempotency_key: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitPaymentLineCreate(BaseModel):
    payment_method: str
    amount: float = Field(gt=0)
    idempotency_key: str | None = None


class SplitPaymentCreate(BaseModel):
    payments: list[SplitPaymentLineCreate]
