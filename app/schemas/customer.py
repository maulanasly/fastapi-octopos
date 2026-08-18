from datetime import datetime

from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    is_active: bool | None = None


class Customer(CustomerBase):
    id: int
    points_balance: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LoyaltyTransaction(BaseModel):
    id: int
    customer_id: int
    order_id: int | None = None
    transaction_type: str
    points_delta: int
    balance_after: int
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
