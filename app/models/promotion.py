from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
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


def _utcnow():
    """Aware-UTC now with microsecond precision (PostgreSQL TIMESTAMPTZ)."""
    return datetime.now(UTC)


class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_promotions_tenant_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String, nullable=False)  # percentage, fixed
    discount_value = Column(Numeric(12, 2), nullable=False)
    min_order_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    max_discount_amount = Column(Numeric(12, 2), nullable=True)
    applies_to = Column(
        String, nullable=False, default="order"
    )  # order, product, category
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    tenant = relationship("Tenant")
    product = relationship("Product")
    category = relationship("Category")
    orders = relationship("Order", back_populates="promotion")
