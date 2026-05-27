from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    payment_method: str
    amount: float = Field(gt=0)


class PaymentCreate(PaymentBase):
    idempotency_key: Optional[str] = None


class Payment(PaymentBase):
    id: int
    order_id: int
    user_id: int
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitPaymentLineCreate(BaseModel):
    payment_method: str
    amount: float = Field(gt=0)


class SplitPaymentCreate(BaseModel):
    payments: List[SplitPaymentLineCreate]
