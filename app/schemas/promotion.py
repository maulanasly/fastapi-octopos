from datetime import datetime

from pydantic import BaseModel, Field


class PromotionBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    discount_type: str
    discount_value: float = Field(ge=0)
    min_order_amount: float = Field(0.0, ge=0)
    max_discount_amount: float | None = Field(None, ge=0)
    applies_to: str = "order"
    product_id: int | None = None
    category_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True
    usage_limit: int | None = Field(None, ge=1)


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    discount_type: str | None = None
    discount_value: float | None = Field(None, ge=0)
    min_order_amount: float | None = Field(None, ge=0)
    max_discount_amount: float | None = Field(None, ge=0)
    applies_to: str | None = None
    product_id: int | None = None
    category_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None
    usage_limit: int | None = Field(None, ge=1)


class Promotion(PromotionBase):
    id: int
    usage_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
