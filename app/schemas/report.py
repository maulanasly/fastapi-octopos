from typing import Optional

from pydantic import BaseModel


class SalesSummary(BaseModel):
    gross_revenue: float
    total_discounts: float
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


class TopCustomerItem(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: Optional[str]
    order_count: int
    total_spent: float
    points_balance: int


class CategorySalesItem(BaseModel):
    category_id: Optional[int]
    category_name: str
    total_revenue: float
    total_quantity_sold: int
