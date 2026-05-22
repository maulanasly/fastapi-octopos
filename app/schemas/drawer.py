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


class DrawerSession(DrawerSessionBase):
    id: int
    user_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    ending_cash: Optional[float] = None
    status: str

    class Config:
        from_attributes = True
