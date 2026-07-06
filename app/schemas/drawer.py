from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class DrawerSessionBase(BaseModel):
    starting_cash: float
    expected_cash: Optional[float] = 0.0


class DrawerSessionCreate(DrawerSessionBase):
    pass


class DrawerSessionClose(BaseModel):
    ending_cash: float
    expected_cash: Optional[float] = None


class ShiftReconciliationCreate(BaseModel):
    counted_cash: float
    counted_non_cash: Optional[float] = None
    notes: Optional[str] = None


class ShiftReconciliation(BaseModel):
    id: int
    drawer_session_id: int
    closed_by_user_id: int
    cash_sales_total: float
    non_cash_sales_total: float
    refunds_total: float
    expected_cash: float
    counted_cash: float
    cash_variance: float
    expected_non_cash: float
    counted_non_cash: float
    non_cash_variance: float
    completed_order_count: int
    gross_sales_total: float
    net_sales_total: float
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DrawerSession(DrawerSessionBase):
    id: int
    user_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    ending_cash: Optional[float] = None
    status: str

    model_config = {"from_attributes": True}
