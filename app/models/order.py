from sqlalchemy import (
    Column,
    DateTime,
    Float,
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
from app.models.types import PointType


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "idempotency_key", name="uq_orders_user_idempotency"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    promotion_id = Column(
        Integer, ForeignKey("promotions.id"), nullable=True, index=True
    )
    drawer_session_id = Column(
        Integer, ForeignKey("drawer_sessions.id"), nullable=True, index=True
    )
    drawer_session = relationship("DrawerSession", back_populates="orders")
    tenant = relationship("Tenant")
    idempotency_key = Column(String, nullable=True, index=True)
    subtotal_amount = Column(Numeric(12, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    taxable_base_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    tax_total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    grand_total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    change_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    remaining_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    redeemed_points = Column(Integer, nullable=False, default=0)
    status = Column(
        String, default="pending", index=True
    )  # pending, completed, cancelled
    serving_status = Column(
        String, nullable=False, default="none", index=True
    )  # none, queued, preparing, ready, served
    preparing_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)
    served_at = Column(DateTime(timezone=True), nullable=True)
    reservation_status = Column(
        String, nullable=False, default="reserved", index=True
    )  # reserved, released, committed
    reservation_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    destination_address = Column(Text, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    destination = Column(PointType, nullable=True)
    tracking_status = Column(
        String, nullable=False, default="none", index=True
    )  # none, assigned, en_route, on_site
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    en_route_at = Column(DateTime(timezone=True), nullable=True)
    on_site_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    customer = relationship("Customer", back_populates="orders")
    promotion = relationship("Promotion", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    refunds = relationship("Refund", back_populates="order")
    tax_lines = relationship("OrderTaxLine", back_populates="order")
    location_updates = relationship(
        "OrderLocationUpdate", back_populates="order", order_by="OrderLocationUpdate.id"
    )

    @property
    def latest_location(self) -> dict | None:
        """Last reported position for the live map (None when untracked)."""
        if not self.location_updates:
            return None
        last = self.location_updates[-1]
        return {
            "lat": last.lat,
            "lng": last.lng,
            "source": last.source,
            "created_at": last.created_at,
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    # Cost snapshot taken at sale time (see migration 0020). NULL for
    # orders created before cost tracking; excluded from margin math.
    unit_cost = Column(Numeric(12, 2), nullable=True)

    tenant = relationship("Tenant")
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    refund_items = relationship("RefundItem", back_populates="order_item")


class OrderLocationUpdate(Base):
    __tablename__ = "order_location_updates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location = Column(PointType, nullable=True)
    source = Column(
        String, nullable=False, default="gps", index=True
    )  # gps, manual, offline
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="location_updates")
