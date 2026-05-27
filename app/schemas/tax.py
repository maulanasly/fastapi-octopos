from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TaxRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    tax_scope: str = "order"
    tax_mode: str = "exclusive"
    rate: float = Field(..., ge=0, le=100)
    category_id: Optional[int] = None
    product_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tax_scope: Optional[str] = None
    tax_mode: Optional[str] = None
    rate: Optional[float] = Field(None, ge=0, le=100)
    category_id: Optional[int] = None
    product_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class TaxRule(TaxRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderTaxLine(BaseModel):
    id: int
    tax_rule_id: Optional[int] = None
    tax_name: str
    tax_scope: str
    tax_mode: str
    tax_rate: float
    taxable_base: float
    tax_amount: float
    applied_at: datetime

    model_config = {"from_attributes": True}


class TaxLiabilityItem(BaseModel):
    tax_name: str
    tax_rate: float
    total_taxable_base: float
    total_tax_amount: float
    order_count: int


class TaxLiabilitySummary(BaseModel):
    total_tax_amount: float
    items: List[TaxLiabilityItem]
