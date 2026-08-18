from datetime import datetime

from pydantic import BaseModel

from app.schemas.product import Category as CategorySchema
from app.schemas.product import Product as ProductSchema
from app.schemas.promotion import Promotion as PromotionSchema
from app.schemas.tax import TaxRule as TaxRuleSchema


class CatalogDelta(BaseModel):
    server_time: datetime
    since: datetime | None = None
    categories: list[CategorySchema] = []
    products: list[ProductSchema] = []
    promotions: list[PromotionSchema] = []
    tax_rules: list[TaxRuleSchema] = []
