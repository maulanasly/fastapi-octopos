from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.core.localization import get_localization_setting
from app.models.localization import LocalizationSetting as LocalizationSettingModel
from app.models.user import User
from app.schemas.localization import LocalizationSetting, LocalizationSettingUpdate

router = APIRouter()


@router.get("/", response_model=LocalizationSetting)
def get_localization_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user
    return get_localization_setting(db)


@router.put("/", response_model=LocalizationSetting)
def update_localization_settings(
    payload: LocalizationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("settings:manage")),
):
    _ = current_user
    setting: LocalizationSettingModel = get_localization_setting(db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
