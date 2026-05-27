from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "idempotency_key", name="uq_orders_user_idempotency"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True)
    drawer_session_id = Column(Integer, ForeignKey("drawer_sessions.id"), nullable=True)
    drawer_session = relationship("DrawerSession", back_populates="orders")
    idempotency_key = Column(String, nullable=True, index=True)
    subtotal_amount = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    redeemed_points = Column(Integer, nullable=False, default=0)
    status = Column(String, default="pending")  # pending, completed, cancelled
    reservation_status = Column(
        String, nullable=False, default="reserved", index=True
    )  # reserved, released, committed
    reservation_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    customer = relationship("Customer", back_populates="orders")
    promotion = relationship("Promotion", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    refunds = relationship("Refund", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    refund_items = relationship("RefundItem", back_populates="order_item")
