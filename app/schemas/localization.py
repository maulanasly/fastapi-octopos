from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LocalizationSettingBase(BaseModel):
    language: str = "en"
    timezone: str = "UTC"
    currency: str = "USD"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    number_format: str = "en_US"
    country_code: str = "US"


class LocalizationSettingUpdate(BaseModel):
    language: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    country_code: Optional[str] = None


class LocalizationSetting(LocalizationSettingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
