import re

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CategoryBase(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _validate_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _HEX_COLOR.match(value):
            raise ValueError("color must be a hex value like #E8F5E9")
        return value.upper()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _validate_color(cls, value: str | None) -> str | None:
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
    description: str | None = None
    price: float
    unit_cost: float | None = None
    stock_quantity: int = Field(0, ge=0)
    min_stock: int = Field(0, ge=0)
    max_stock: int | None = Field(None, ge=0)
    reorder_point: int = Field(0, ge=0)
    lead_time_days: int = Field(0, ge=0)
    category_id: int | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: str | None = None
    sku: str | None = None
    price: float | None = None


class Product(ProductBase):
    id: int
    category: Category | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}
