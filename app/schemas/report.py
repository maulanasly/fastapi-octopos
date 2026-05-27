from typing import Optional

from pydantic import BaseModel


class SalesSummary(BaseModel):
    total_revenue: float
    total_refunds: float
    net_revenue: float
    order_count: int
    average_order_value: float


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    product_sku: str
    total_quantity_sold: int
    total_revenue: float


class CategorySalesItem(BaseModel):
    category_id: Optional[int]
    category_name: str
    total_revenue: float
    total_quantity_sold: int
