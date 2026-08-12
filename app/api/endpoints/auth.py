from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.rbac import assign_default_cashier_role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate

router = APIRouter()


class GoogleToken(BaseModel):
    token: str


def _issue_tokens(user: User, db: Session) -> dict:
    """Create and persist an access + refresh token pair for a user."""
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete(
        synchronize_session=False
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.id, expires_delta=access_token_expires)

    raw_refresh, expires_at = create_refresh_token()
    db_refresh = RefreshToken(
        token=hash_refresh_token(raw_refresh), user_id=user.id, expires_at=expires_at
    )
    db.add(db_refresh)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": raw_refresh,
    }


@router.post(
    "/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.
    """
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    assign_default_cashier_role(db=db, user=user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 compatible token login. Returns access + refresh tokens.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return _issue_tokens(user, db)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh_access_token(
    request: Request, payload: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    The old refresh token is revoked.
    """
    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == hash_refresh_token(payload.refresh_token),
            RefreshToken.revoked == False,  # noqa: E712
        )  # noqa: E712
        .first()
    )
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Revoke the used token (rotation)
    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db.add(db_token)

    return _issue_tokens(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Revoke the given refresh token (server-side logout).
    """
    db_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == hash_refresh_token(payload.refresh_token))
        .first()
    )
    if db_token:
        db_token.revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db.add(db_token)
        db.commit()


@router.post("/google", response_model=Token)
@limiter.limit("10/minute")
def google_auth(
    request: Request, google_token: GoogleToken, db: Session = Depends(get_db)
):
    """
    Verify Google ID token and return a local access + refresh token pair.
    """
    try:
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("Google Client ID not configured")

        idinfo = id_token.verify_oauth2_token(
            google_token.token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]
        name = idinfo.get("name", "")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, full_name=name, is_active=True)
            db.add(user)
            assign_default_cashier_role(db=db, user=user)
            db.commit()
            db.refresh(user)

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        return _issue_tokens(user, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
        )
