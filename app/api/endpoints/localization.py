from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.core.localization import (
    REGION_PRESETS,
    get_localization_setting,
    resolve_user_localization,
)
from app.models.localization import LocalizationSetting as LocalizationSettingModel
from app.models.user import User
from app.schemas.localization import LocalizationSetting, LocalizationSettingUpdate

router = APIRouter()


class RegionInfo(BaseModel):
    country_code: str
    language: str
    timezone: str
    currency: str
    date_format: str
    number_format: str


class MyRegionUpdate(BaseModel):
    region: str | None = Field(
        None, description='Regional preset country code ("US", "ID") or null to reset'
    )


@router.get("/regions", response_model=list[RegionInfo])
def list_region_presets(
    current_user: User = Depends(get_current_active_user),
):
    """Supported regional presets users can opt into."""
    _ = current_user
    return [
        RegionInfo(country_code=code, **preset)
        for code, preset in REGION_PRESETS.items()
    ]


@router.get("/me", response_model=LocalizationSetting)
def get_my_localization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Effective per-user localization (preset or global default)."""
    return resolve_user_localization(db, current_user)


@router.put("/me", response_model=LocalizationSetting)
def update_my_localization(
    payload: MyRegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Switch the caller's region preset (or reset to the global default)."""
    if payload.region is not None:
        code = payload.region.strip().upper()
        if code not in REGION_PRESETS:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported region. Supported: {', '.join(REGION_PRESETS)}",
            )
        payload.region = code
    current_user.region = payload.region
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return resolve_user_localization(db, current_user)


@router.get("/", response_model=LocalizationSetting)
def get_localization_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user
    return get_localization_setting(db, current_user.tenant_id)


@router.put("/", response_model=LocalizationSetting)
def update_localization_settings(
    payload: LocalizationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("settings:manage")),
):
    _ = current_user
    setting: LocalizationSettingModel = get_localization_setting(
        db, current_user.tenant_id
    )
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    # Indonesia regional preset: picking the IDR currency or the ID country
    # code implies the id_ID number format (".", thousands; ",", decimal)
    # unless the caller explicitly chose a different one.
    if "number_format" not in update_data and (
        setting.currency.upper() == "IDR" or setting.country_code.upper() == "ID"
    ):
        setting.number_format = "id_ID"

    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
