from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


def _utcnow_naive():
    """Naive-UTC now with microsecond precision (SQLite stores naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # hex, e.g. "#E8F5E9"
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    stock_quantity = Column(Integer, default=0)
    min_stock = Column(Integer, nullable=False, default=0)
    max_stock = Column(Integer, nullable=True)
    reorder_point = Column(Integer, nullable=False, default=0)
    lead_time_days = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String, nullable=True)  # /media/... path
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )

    category = relationship("Category", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
