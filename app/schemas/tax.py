from datetime import datetime

from pydantic import BaseModel, Field


class TaxRuleBase(BaseModel):
    name: str
    description: str | None = None
    tax_scope: str = "order"
    tax_mode: str = "exclusive"
    rate: float = Field(..., ge=0, le=100)
    category_id: int | None = None
    product_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tax_scope: str | None = None
    tax_mode: str | None = None
    rate: float | None = Field(None, ge=0, le=100)
    category_id: int | None = None
    product_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


class TaxRule(TaxRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderTaxLine(BaseModel):
    id: int
    tax_rule_id: int | None = None
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
    items: list[TaxLiabilityItem]
