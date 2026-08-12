from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


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

    model_config = {"from_attributes": True}
