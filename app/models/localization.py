from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class LocalizationSetting(Base):
    __tablename__ = "localization_settings"

    id = Column(Integer, primary_key=True, index=True)
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
