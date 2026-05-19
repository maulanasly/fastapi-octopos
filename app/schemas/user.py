from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int

    model_config = {"from_attributes": True}
