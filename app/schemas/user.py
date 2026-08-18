# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.rbac import Role

MIN_PASSWORD_LENGTH = 8


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower().strip()


class UserCreate(UserBase):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    tenant_id: int | None = None  # superuser-only: target tenant for staff creation

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        return value


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=MIN_PASSWORD_LENGTH)

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.lower().strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        return value


class User(UserBase):
    id: int
    tenant_id: int | None = None
    roles: list[Role] = []

    model_config = {"from_attributes": True}
