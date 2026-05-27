from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class Customer(CustomerBase):
    id: int
    points_balance: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LoyaltyTransaction(BaseModel):
    id: int
    customer_id: int
    order_id: Optional[int] = None
    transaction_type: str
    points_delta: int
    balance_after: int
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
