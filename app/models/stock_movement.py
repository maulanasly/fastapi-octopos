from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    order_item_id = Column(
        Integer, ForeignKey("order_items.id"), nullable=True, index=True
    )
    purchase_order_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=True, index=True
    )
    purchase_order_item_id = Column(
        Integer, ForeignKey("purchase_order_items.id"), nullable=True, index=True
    )
    refund_id = Column(Integer, ForeignKey("refunds.id"), nullable=True, index=True)
    movement_type = Column(String, nullable=False, index=True)
    quantity_before = Column(Integer, nullable=False)
    quantity_delta = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    product = relationship("Product", back_populates="stock_movements")
    user = relationship("User")
    order = relationship("Order")
    order_item = relationship("OrderItem")
    purchase_order = relationship("PurchaseOrder")
    purchase_order_item = relationship("PurchaseOrderItem")
    refund = relationship("Refund")
