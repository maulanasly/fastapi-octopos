from datetime import datetime

from pydantic import BaseModel


class LocalizationSettingBase(BaseModel):
    language: str = "en"
    timezone: str = "UTC"
    currency: str = "USD"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    number_format: str = "en_US"
    country_code: str = "US"


class LocalizationSettingUpdate(BaseModel):
    language: str | None = None
    timezone: str | None = None
    currency: str | None = None
    date_format: str | None = None
    number_format: str | None = None
    country_code: str | None = None


class LocalizationSetting(LocalizationSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
