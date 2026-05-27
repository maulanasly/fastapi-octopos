from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PromotionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float = Field(ge=0)
    min_order_amount: float = Field(0.0, ge=0)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    applies_to: str = "order"
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True
    usage_limit: Optional[int] = Field(None, ge=1)


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = Field(None, ge=0)
    min_order_amount: Optional[float] = Field(None, ge=0)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    applies_to: Optional[str] = None
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    usage_limit: Optional[int] = Field(None, ge=1)


class Promotion(PromotionBase):
    id: int
    usage_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
