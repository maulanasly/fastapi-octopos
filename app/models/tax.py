from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    tax_scope = Column(String, nullable=False, default="order", index=True)
    tax_mode = Column(String, nullable=False, default="exclusive", index=True)
    rate = Column(Float, nullable=False, default=0.0)
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    category = relationship("Category")
    product = relationship("Product")
    order_tax_lines = relationship("OrderTaxLine", back_populates="tax_rule")


class OrderTaxLine(Base):
    __tablename__ = "order_tax_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    tax_rule_id = Column(Integer, ForeignKey("tax_rules.id"), nullable=True, index=True)
    tax_name = Column(String, nullable=False)
    tax_scope = Column(String, nullable=False)
    tax_mode = Column(String, nullable=False)
    tax_rate = Column(Float, nullable=False)
    taxable_base = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    applied_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="tax_lines")
    tax_rule = relationship("TaxRule", back_populates="order_tax_lines")
