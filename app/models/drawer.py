from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DrawerSession(Base):
    __tablename__ = "drawer_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opened_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at = Column(DateTime(timezone=True), nullable=True)
    starting_cash = Column(Float, default=0.0, nullable=False)
    ending_cash = Column(Float, nullable=True)
    expected_cash = Column(Float, default=0.0, nullable=False)
    status = Column(String, default="open", nullable=False)  # "open", "closed"

    user = relationship("User")
    orders = relationship("Order", back_populates="drawer_session")
