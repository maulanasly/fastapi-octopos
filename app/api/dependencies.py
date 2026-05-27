# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, Request, status

# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

# pyrefly: ignore [missing-import]
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import parse_language, t
from app.models.rbac import Permission, RolePermission, UserRole
from app.models.user import User
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    language = parse_language(request.headers.get("accept-language"))
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.invalid_credentials", language),
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail=t("auth.user_not_found", language))
    return user


def get_current_active_user(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    language = parse_language(request.headers.get("accept-language"))
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail=t("auth.inactive_user", language))
    return current_user


def get_current_active_superuser(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> User:
    language = parse_language(request.headers.get("accept-language"))
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail=t("auth.insufficient_privileges", language),
        )
    return current_user


def _get_user_permission_codes(db: Session, user_id: int) -> set[str]:
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def has_permission(db: Session, user: User, permission_code: str) -> bool:
    if user.is_superuser:
        return True
    return permission_code in _get_user_permission_codes(db=db, user_id=user.id)


def require_permissions(*permission_codes: str):
    def _checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        language = parse_language(request.headers.get("accept-language"))
        if current_user.is_superuser:
            return current_user

        user_permission_codes = _get_user_permission_codes(
            db=db, user_id=current_user.id
        )
        missing_permissions = [
            permission_code
            for permission_code in permission_codes
            if permission_code not in user_permission_codes
        ]
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t("auth.insufficient_privileges", language),
            )
        return current_user

    return _checker
