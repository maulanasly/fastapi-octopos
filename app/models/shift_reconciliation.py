from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ShiftReconciliation(Base):
    __tablename__ = "shift_reconciliations"

    id = Column(Integer, primary_key=True, index=True)
    drawer_session_id = Column(
        Integer,
        ForeignKey("drawer_sessions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    closed_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    cash_sales_total = Column(Float, nullable=False, default=0.0)
    non_cash_sales_total = Column(Float, nullable=False, default=0.0)
    refunds_total = Column(Float, nullable=False, default=0.0)
    expected_cash = Column(Float, nullable=False, default=0.0)
    counted_cash = Column(Float, nullable=False, default=0.0)
    cash_variance = Column(Float, nullable=False, default=0.0)
    expected_non_cash = Column(Float, nullable=False, default=0.0)
    counted_non_cash = Column(Float, nullable=False, default=0.0)
    non_cash_variance = Column(Float, nullable=False, default=0.0)
    completed_order_count = Column(Integer, nullable=False, default=0)
    gross_sales_total = Column(Float, nullable=False, default=0.0)
    net_sales_total = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drawer_session = relationship("DrawerSession", back_populates="reconciliation")
    closed_by_user = relationship("User")
