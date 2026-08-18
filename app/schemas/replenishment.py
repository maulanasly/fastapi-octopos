from pydantic import BaseModel, Field


class ReplenishmentSuggestion(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    min_stock: int
    max_stock: int | None = None
    reorder_point: int
    lead_time_days: int
    lookback_days: int
    sold_quantity: int
    daily_sales_velocity: float
    projected_stock_at_lead_time: int
    suggested_target_stock: int
    recommended_order_quantity: int
    should_reorder: bool


class PurchaseOrderFromSuggestionsCreate(BaseModel):
    supplier_id: int
    lookback_days: int = Field(30, ge=1, le=365)
    product_ids: list[int] | None = None
    include_only_reorder: bool = True
    notes: str | None = None
