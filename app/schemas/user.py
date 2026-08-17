from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field, field_validator

MIN_PASSWORD_LENGTH = 8


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower().strip()


class UserCreate(UserBase):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        return value


class UserUpdate(UserBase):
    password: Optional[str] = Field(default=None, min_length=MIN_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        return value


class User(UserBase):
    id: int

    model_config = {"from_attributes": True}
