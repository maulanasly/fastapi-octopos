from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DrawerSession(Base):
    __tablename__ = "drawer_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opened_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at = Column(DateTime(timezone=True), nullable=True)
    starting_cash = Column(Numeric(12, 2), default=0.0, nullable=False)
    ending_cash = Column(Numeric(12, 2), nullable=True)
    expected_cash = Column(Numeric(12, 2), default=0.0, nullable=False)
    status = Column(String, default="open", nullable=False)  # "open", "closed"

    user = relationship("User")
    orders = relationship("Order", back_populates="drawer_session")
    reconciliation = relationship(
        "ShiftReconciliation", back_populates="drawer_session", uselist=False
    )
