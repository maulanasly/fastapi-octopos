import re
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

    @field_validator("color")
    @classmethod
    def _validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not _HEX_COLOR.match(value):
            raise ValueError("color must be a hex value like #E8F5E9")
        return value.upper()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

    @field_validator("color")
    @classmethod
    def _validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not _HEX_COLOR.match(value):
            raise ValueError("color must be a hex value like #E8F5E9")
        return value.upper()


class Category(CategoryBase):
    id: int

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    sku: str
    description: Optional[str] = None
    price: float
    unit_cost: Optional[float] = None
    stock_quantity: int = Field(0, ge=0)
    min_stock: int = Field(0, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    reorder_point: int = Field(0, ge=0)
    lead_time_days: int = Field(0, ge=0)
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None


class Product(ProductBase):
    id: int
    category: Optional[Category] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    model_config = {"from_attributes": True}
