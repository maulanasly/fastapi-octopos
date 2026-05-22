from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DrawerSession(Base):
    __tablename__ = "drawer_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    starting_cash = Column(Float, default=0.0, nullable=False)
    ending_cash = Column(Float, nullable=True)
    expected_cash = Column(Float, default=0.0, nullable=False)
    status = Column(String, default="open", nullable=False)  # "open", "closed"

    user = relationship("User")
    orders = relationship("Order", back_populates="drawer_session")
