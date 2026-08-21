from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class PurchasingSetting(Base):
    """Per-tenant automation settings for the scheduled auto-PO task."""

    __tablename__ = "purchasing_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_purchasing_settings_tenant_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    tenant = relationship("Tenant")
    auto_po_enabled = Column(Boolean, nullable=False, default=False)
    auto_po_lookback_days = Column(Integer, nullable=False, default=30)
    # Products at/below max(reorder_point, min_stock_trigger) become
    # candidates; 0 keeps the product-level reorder point as the only line.
    auto_po_min_stock_trigger = Column(Integer, nullable=False, default=0)
