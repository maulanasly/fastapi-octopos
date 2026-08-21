from pydantic import BaseModel, Field

from app.schemas.purchase import PurchaseOrder as PurchaseOrderSchema


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
    unit_cost: float = 0
    suggested_supplier_id: int | None = None
    suggested_supplier_name: str | None = None


class PurchaseOrderFromSuggestionsCreate(BaseModel):
    supplier_id: int
    lookback_days: int = Field(30, ge=1, le=365)
    product_ids: list[int] | None = None
    include_only_reorder: bool = True
    notes: str | None = None


class ReplenishmentItemOverride(BaseModel):
    product_id: int
    quantity_ordered: int | None = Field(None, ge=1)
    unit_cost: float | None = Field(None, ge=0)
    supplier_id: int | None = None


class PurchaseOrderBatchFromSuggestionsCreate(BaseModel):
    lookback_days: int = Field(30, ge=1, le=365)
    product_ids: list[int] | None = None
    items: list[ReplenishmentItemOverride] | None = None
    notes: str | None = None


class SkippedProduct(BaseModel):
    product_id: int
    reason: str


class PurchaseOrderBatchFromSuggestionsResponse(BaseModel):
    purchase_orders: list[PurchaseOrderSchema]
    skipped_products: list[SkippedProduct]
