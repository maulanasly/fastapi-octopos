from datetime import UTC, datetime

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
from app.models.types import VectorType


def _utcnow():
    """Aware-UTC now with microsecond precision (PostgreSQL TIMESTAMPTZ)."""
    return datetime.now(UTC)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # hex, e.g. "#E8F5E9"
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    tenant = relationship("Tenant")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    stock_quantity = Column(Integer, default=0)
    min_stock = Column(Integer, nullable=False, default=0)
    max_stock = Column(Integer, nullable=True)
    reorder_point = Column(Integer, nullable=False, default=0)
    lead_time_days = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    image_url = Column(String, nullable=True)  # /media/... path
    thumbnail_url = Column(String, nullable=True)  # /media/... WebP thumbnail
    embedding = Column(VectorType(384), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    tenant = relationship("Tenant")
    category = relationship("Category", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
