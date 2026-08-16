from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class SalesSummary(BaseModel):
    gross_revenue: float
    total_discounts: float
    total_revenue: float
    total_refunds: float
    net_revenue: float
    order_count: int
    average_order_value: float


class PaymentBreakdownItem(BaseModel):
    payment_method: str
    count: int
    amount: float


class ShiftReport(BaseModel):
    reconciliation_id: int
    drawer_session_id: int
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]
    operator_name: Optional[str]
    closed_by_name: Optional[str]
    starting_cash: float
    expected_cash: float
    counted_cash: float
    cash_variance: float
    expected_non_cash: float
    counted_non_cash: float
    non_cash_variance: float
    cash_sales_total: float
    non_cash_sales_total: float
    refunds_total: float
    gross_sales_total: float
    net_sales_total: float
    completed_order_count: int
    payment_breakdown: List[PaymentBreakdownItem] = []


class DailyShiftItem(BaseModel):
    reconciliation_id: int
    drawer_session_id: int
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]
    operator_name: Optional[str]
    cash_sales_total: float
    non_cash_sales_total: float
    refunds_total: float
    gross_sales_total: float
    net_sales_total: float
    completed_order_count: int
    cash_variance: float


class DailyCloseTotals(BaseModel):
    gross_sales_total: float
    net_sales_total: float
    cash_sales_total: float
    non_cash_sales_total: float
    refunds_total: float
    cash_variance: float
    non_cash_variance: float
    completed_order_count: int
    shift_count: int


class DailyClose(BaseModel):
    date: str
    totals: DailyCloseTotals
    shifts: List[DailyShiftItem]


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
