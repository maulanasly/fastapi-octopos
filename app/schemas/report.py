from datetime import datetime

from pydantic import BaseModel


class SalesSummary(BaseModel):
    gross_revenue: float
    total_discounts: float
    total_revenue: float
    total_refunds: float
    net_revenue: float
    order_count: int
    average_order_value: float
    # Per-sale COGS from the order_items.unit_cost snapshot (migration
    # 0020). cogs_known_ratio < 1 means some sold lines had no cost
    # snapshot, so the margin is computed over known-cost lines only.
    cogs_total: float = 0.0
    gross_margin_amount: float = 0.0
    gross_margin_percent: float | None = None
    cogs_known_ratio: float | None = None


class PaymentBreakdownItem(BaseModel):
    payment_method: str
    count: int
    amount: float


class ShiftReport(BaseModel):
    reconciliation_id: int
    drawer_session_id: int
    opened_at: datetime | None
    closed_at: datetime | None
    operator_name: str | None
    closed_by_name: str | None
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
    payment_breakdown: list[PaymentBreakdownItem] = []


class DailyShiftItem(BaseModel):
    reconciliation_id: int
    drawer_session_id: int
    opened_at: datetime | None
    closed_at: datetime | None
    operator_name: str | None
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
    shifts: list[DailyShiftItem]


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    product_sku: str
    total_quantity_sold: int
    total_revenue: float


class TopCustomerItem(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: str | None
    order_count: int
    total_spent: float
    points_balance: int


class CategorySalesItem(BaseModel):
    category_id: int | None
    category_name: str
    total_revenue: float
    total_quantity_sold: int


class SupplierSpendItem(BaseModel):
    supplier_id: int
    supplier_name: str
    po_count: int
    invoice_count: int
    approved_total: float
    variance_total: float


class SupplierSpendSummary(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    cogs_estimate: float = 0.0
    items: list[SupplierSpendItem] = []


class VarianceTrendItem(BaseModel):
    period: str  # YYYY-MM
    invoice_count: int
    billed_total: float
    approved_total: float
    variance_total: float


class VarianceTrendSummary(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    months: list[VarianceTrendItem] = []
