from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LocalizationSetting(Base):
    __tablename__ = "localization_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_localization_settings_tenant_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant")
    language = Column(String, nullable=False, default="en")
    timezone = Column(String, nullable=False, default="UTC")
    currency = Column(String, nullable=False, default="USD")
    date_format = Column(String, nullable=False, default="%Y-%m-%d %H:%M:%S")
    number_format = Column(String, nullable=False, default="en_US")
    country_code = Column(String, nullable=False, default="US")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
