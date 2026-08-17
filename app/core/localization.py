from datetime import datetime, timezone
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.localization import LocalizationSetting
from app.models.user import User

# Regional presets keyed by country_code. A user with users.region set
# resolves their full localization from here, overriding the global
# singleton LocalizationSetting.
REGION_PRESETS: Dict[str, Dict[str, str]] = {
    "US": {
        "language": "en",
        "timezone": "UTC",
        "currency": "USD",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "number_format": "en_US",
    },
    "ID": {
        "language": "id",
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "date_format": "%d-%m-%Y %H:%M",
        "number_format": "id_ID",
    },
}


def get_localization_setting(
    db: Session, tenant_id: Optional[int] = None
) -> LocalizationSetting:
    query = db.query(LocalizationSetting).order_by(LocalizationSetting.id.asc())
    if tenant_id is not None:
        query = query.filter(LocalizationSetting.tenant_id == tenant_id)
    setting = query.first()
    if setting:
        return setting

    # Platform-level (admin) lookups without a tenant default to tenant 1.
    setting = LocalizationSetting(tenant_id=tenant_id or 1)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def resolve_user_localization(db: Session, user: User) -> LocalizationSetting:
    """Effective localization for a user.

    A user with ``region`` set gets the preset's values; otherwise the
    tenant's LocalizationSetting applies.
    """
    tenant_id = user.tenant_id
    preset = REGION_PRESETS.get(user.region.upper() if user.region else "")
    if not preset:
        return get_localization_setting(db, tenant_id)

    tenant_setting = get_localization_setting(db, tenant_id)
    return LocalizationSetting(
        language=preset["language"],
        timezone=preset["timezone"],
        currency=preset["currency"],
        date_format=preset["date_format"],
        number_format=preset["number_format"],
        country_code=user.region.upper(),
        id=tenant_setting.id,
        tenant_id=tenant_id,
        created_at=tenant_setting.created_at,
        updated_at=tenant_setting.updated_at,
    )


def format_number(value: float, number_format: str) -> str:
    if number_format == "id_ID":
        formatted = f"{value:,.2f}"
        return formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{value:,.2f}"


def format_currency(value: float, currency: str, number_format: str) -> str:
    symbols = {
        "USD": "$",
        "IDR": "Rp",
        "EUR": "€",
        "GBP": "£",
        "SGD": "S$",
        "JPY": "¥",
        "MYR": "RM",
        "AUD": "A$",
    }
    symbol = symbols.get(currency.upper(), currency.upper())
    amount = format_number(value, number_format)
    if currency.upper() == "IDR":
        amount = (
            amount.split(",")[0] if number_format == "id_ID" else amount.split(".")[0]
        )
        # Indonesian convention: a space between "Rp" and the amount.
        return f"{symbol} {amount}"
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
