from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.localization import LocalizationSetting


def get_localization_setting(db: Session) -> LocalizationSetting:
    setting = (
        db.query(LocalizationSetting).order_by(LocalizationSetting.id.asc()).first()
    )
    if setting:
        return setting

    setting = LocalizationSetting()
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def format_number(value: float, number_format: str) -> str:
    if number_format == "id_ID":
        formatted = f"{value:,.2f}"
        return formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{value:,.2f}"


def format_currency(value: float, currency: str, number_format: str) -> str:
    symbols = {"USD": "$", "IDR": "Rp", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency.upper(), currency.upper())
    amount = format_number(value, number_format)
    if currency.upper() == "IDR":
        amount = (
            amount.split(",")[0] if number_format == "id_ID" else amount.split(".")[0]
        )
    return f"{symbol}{amount}"


def format_datetime(
    dt: Optional[datetime],
    tz_name: str,
    date_format: str,
) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        zoned = dt.astimezone(ZoneInfo(tz_name))
    except Exception:
        zoned = dt.astimezone(timezone.utc)
    return zoned.strftime(date_format)
