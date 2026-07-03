from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "idempotency_key", name="uq_refunds_user_idempotency"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    idempotency_key = Column(String, nullable=True, index=True)
    reason = Column(Text, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="refunds")
    user = relationship("User")
    items = relationship("RefundItem", back_populates="refund")


class RefundItem(Base):
    __tablename__ = "refund_items"

    id = Column(Integer, primary_key=True, index=True)
    refund_id = Column(Integer, ForeignKey("refunds.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)

    refund = relationship("Refund", back_populates="items")
    order_item = relationship("OrderItem", back_populates="refund_items")
    product = relationship("Product")
