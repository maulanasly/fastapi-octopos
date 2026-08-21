from pydantic import BaseModel, Field


class PurchasingSettingRead(BaseModel):
    tenant_id: int
    auto_po_enabled: bool
    auto_po_lookback_days: int
    auto_po_min_stock_trigger: int

    model_config = {"from_attributes": True}


class PurchasingSettingUpdate(BaseModel):
    auto_po_enabled: bool | None = None
    auto_po_lookback_days: int | None = Field(None, ge=1, le=365)
    auto_po_min_stock_trigger: int | None = Field(None, ge=0)
