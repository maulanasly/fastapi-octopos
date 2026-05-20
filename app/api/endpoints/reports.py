from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser
from app.core.database import get_db
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.user import User
from app.schemas.product import Product as ProductSchema
from app.schemas.report import CategorySalesItem, SalesSummary, TopProductItem

router = APIRouter()


@router.get("/sales", response_model=SalesSummary)
def get_sales_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_superuser),
):
    query = db.query(
        func.coalesce(func.sum(Order.total_amount), 0.0), func.count(Order.id)
    ).filter(Order.status == "completed")

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    total_revenue, order_count = query.first()

    average_order_value = total_revenue / order_count if order_count > 0 else 0.0

    return SalesSummary(
        total_revenue=float(total_revenue),
        order_count=int(order_count),
        average_order_value=float(average_order_value),
    )


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(get_current_active_superuser),
):
    query = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.sku.label("product_sku"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
        )
        .select_from(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    query = (
        query.group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    results = query.all()

    return [
        TopProductItem(
            product_id=row.product_id,
            product_name=row.product_name,
            product_sku=row.product_sku,
            total_quantity_sold=int(row.total_quantity_sold or 0),
            total_revenue=float(row.total_revenue or 0.0),
        )
        for row in results
    ]


@router.get("/categories", response_model=List[CategorySalesItem])
def get_category_sales(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_superuser),
):
    query = (
        db.query(
            Category.id.label("category_id"),
            func.coalesce(Category.name, "Uncategorized").label("category_name"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
        )
        .select_from(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    query = query.group_by(Category.id, Category.name).order_by(
        func.sum(OrderItem.quantity * OrderItem.unit_price).desc()
    )

    results = query.all()

    return [
        CategorySalesItem(
            category_id=row.category_id,
            category_name=row.category_name,
            total_revenue=float(row.total_revenue or 0.0),
            total_quantity_sold=int(row.total_quantity_sold or 0),
        )
        for row in results
    ]


@router.get("/low-stock", response_model=List[ProductSchema])
def get_low_stock_products(
    db: Session = Depends(get_db),
    threshold: int = Query(10, ge=0),
    current_user: User = Depends(get_current_active_superuser),
):
    products = db.query(Product).filter(Product.stock_quantity <= threshold).all()
    return products
