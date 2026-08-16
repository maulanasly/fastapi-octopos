from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.product import Category as CategorySchema
from app.schemas.product import Product as ProductSchema
from app.schemas.promotion import Promotion as PromotionSchema
from app.schemas.tax import TaxRule as TaxRuleSchema


class CatalogDelta(BaseModel):
    server_time: datetime
    since: Optional[datetime] = None
    categories: List[CategorySchema] = []
    products: List[ProductSchema] = []
    promotions: List[PromotionSchema] = []
    tax_rules: List[TaxRuleSchema] = []
