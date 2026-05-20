# pyrefly: ignore [missing-import]
from fastapi import APIRouter

from app.api.endpoints import auth, orders, products, reports

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
