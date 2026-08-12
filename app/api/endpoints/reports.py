from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.models.order import Order
from app.models.tax import OrderTaxLine as OrderTaxLineModel
from app.models.user import User
from app.schemas.product import Product as ProductSchema
from app.schemas.purchase import PurchaseInvoiceSummary
from app.schemas.report import (
    CategorySalesItem,
    SalesSummary,
    TopCustomerItem,
    TopProductItem,
)
from app.schemas.tax import TaxLiabilityItem, TaxLiabilitySummary
from app.services.reports import (
    get_category_sales_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_top_customers_data,
    get_top_products_data,
)

router = APIRouter()


@router.get("/sales", response_model=SalesSummary)
def get_sales_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    cashier_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    return SalesSummary(
        **get_sales_summary_data(
            db=db,
            start_date=start_date,
            end_date=end_date,
            cashier_id=cashier_id,
        )
    )


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    rows = get_top_products_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [
        TopProductItem(
            product_id=row.product_id,
            product_name=row.product_name,
            product_sku=row.product_sku,
            total_quantity_sold=int(row.total_quantity_sold or 0),
            total_revenue=float(row.total_revenue or 0.0),
        )
        for row in rows
    ]


@router.get("/categories", response_model=List[CategorySalesItem])
def get_category_sales(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_permissions("reports:view")),
):
    rows = get_category_sales_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
    return [
        CategorySalesItem(
            category_id=row.category_id,
            category_name=row.category_name,
            total_revenue=float(row.total_revenue or 0.0),
            total_quantity_sold=int(row.total_quantity_sold or 0),
        )
        for row in rows
    ]


@router.get("/low-stock", response_model=List[ProductSchema])
def get_low_stock_products(
    db: Session = Depends(get_db),
    threshold: int = Query(10, ge=0),
    current_user: User = Depends(require_permissions("reports:view")),
):
    return get_low_stock_products_data(db=db, threshold=threshold)


@router.get("/top-customers", response_model=List[TopCustomerItem])
def get_top_customers(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    rows = get_top_customers_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [
        TopCustomerItem(
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            customer_email=row.customer_email,
            order_count=int(row.order_count or 0),
            total_spent=float(row.total_spent or 0.0),
            points_balance=int(row.points_balance or 0),
        )
        for row in rows
    ]


@router.get("/purchase-invoices", response_model=PurchaseInvoiceSummary)
def get_purchase_invoice_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    supplier_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    return PurchaseInvoiceSummary(
        **get_invoice_summary_data(
            db=db,
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
        )
    )


@router.get("/tax-liability", response_model=TaxLiabilitySummary)
def get_tax_liability_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_permissions("reports:view")),
):
    query = (
        db.query(
            OrderTaxLineModel.tax_name.label("tax_name"),
            OrderTaxLineModel.tax_rate.label("tax_rate"),
            func.coalesce(func.sum(OrderTaxLineModel.taxable_base), 0.0).label(
                "total_taxable_base"
            ),
            func.coalesce(func.sum(OrderTaxLineModel.tax_amount), 0.0).label(
                "total_tax_amount"
            ),
            func.count(func.distinct(OrderTaxLineModel.order_id)).label("order_count"),
        )
        .join(Order, Order.id == OrderTaxLineModel.order_id)
        .filter(Order.status == "completed")
    )
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    rows = (
        query.group_by(OrderTaxLineModel.tax_name, OrderTaxLineModel.tax_rate)
        .order_by(func.sum(OrderTaxLineModel.tax_amount).desc())
        .all()
    )
    items = [
        TaxLiabilityItem(
            tax_name=row.tax_name,
            tax_rate=float(row.tax_rate or 0.0),
            total_taxable_base=float(row.total_taxable_base or 0.0),
            total_tax_amount=float(row.total_tax_amount or 0.0),
            order_count=int(row.order_count or 0),
        )
        for row in rows
    ]
    total_tax_amount = sum(item.total_tax_amount for item in items)
    return TaxLiabilitySummary(
        total_tax_amount=float(total_tax_amount),
        items=items,
    )
