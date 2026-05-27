from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.purchase import PurchaseInvoice
from app.models.refund import Refund
from app.models.tax import OrderTaxLine
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

router = APIRouter()


@router.get("/sales", response_model=SalesSummary)
def get_sales_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    cashier_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    sales_query = db.query(
        func.coalesce(
            func.sum(func.coalesce(Order.subtotal_amount, Order.total_amount)), 0.0
        ),
        func.coalesce(func.sum(Order.discount_amount), 0.0),
        func.coalesce(func.sum(Order.total_amount), 0.0),
        func.count(Order.id),
    ).filter(Order.status == "completed")
    refunds_query = (
        db.query(func.coalesce(func.sum(Refund.total_amount), 0.0))
        .join(Order, Refund.order_id == Order.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        sales_query = sales_query.filter(Order.created_at >= start_date)
        refunds_query = refunds_query.filter(Refund.created_at >= start_date)
    if end_date:
        sales_query = sales_query.filter(Order.created_at <= end_date)
        refunds_query = refunds_query.filter(Refund.created_at <= end_date)
    if cashier_id:
        sales_query = sales_query.filter(Order.user_id == cashier_id)
        refunds_query = refunds_query.filter(Order.user_id == cashier_id)

    gross_revenue, total_discounts, total_revenue, order_count = sales_query.first()
    total_refunds = float(refunds_query.scalar() or 0.0)
    net_revenue = float(total_revenue or 0.0) - total_refunds

    average_order_value = total_revenue / order_count if order_count > 0 else 0.0

    return SalesSummary(
        gross_revenue=float(gross_revenue),
        total_discounts=float(total_discounts),
        total_revenue=float(total_revenue),
        total_refunds=total_refunds,
        net_revenue=net_revenue,
        order_count=int(order_count),
        average_order_value=float(average_order_value),
    )


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
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
    current_user: User = Depends(require_permissions("reports:view")),
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
    current_user: User = Depends(require_permissions("reports:view")),
):
    products = db.query(Product).filter(Product.stock_quantity <= threshold).all()
    return products


@router.get("/top-customers", response_model=List[TopCustomerItem])
def get_top_customers(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(require_permissions("reports:view")),
):
    query = (
        db.query(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            Customer.email.label("customer_email"),
            Customer.points_balance.label("points_balance"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .filter(Order.status == "completed")
    )

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    rows = (
        query.group_by(
            Customer.id, Customer.name, Customer.email, Customer.points_balance
        )
        .order_by(func.sum(Order.total_amount).desc())
        .limit(limit)
        .all()
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
    query = db.query(PurchaseInvoice)
    if start_date:
        query = query.filter(PurchaseInvoice.created_at >= start_date)
    if end_date:
        query = query.filter(PurchaseInvoice.created_at <= end_date)
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)

    rows = query.with_entities(
        func.count(PurchaseInvoice.id),
        func.coalesce(
            func.sum(
                case(
                    (
                        PurchaseInvoice.status == "approved",
                        PurchaseInvoice.total_amount,
                    ),
                    else_=0.0,
                )
            ),
            0.0,
        ),
        func.coalesce(func.sum(PurchaseInvoice.total_amount), 0.0),
        func.coalesce(func.sum(PurchaseInvoice.variance_amount), 0.0),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "approved", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "rejected", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "pending_review", 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((PurchaseInvoice.status == "draft", 1), else_=0)),
            0,
        ),
    ).first()

    (
        invoice_count,
        approved_total,
        billed_total,
        variance_total,
        approved_count,
        rejected_count,
        pending_review_count,
        draft_count,
    ) = rows

    return PurchaseInvoiceSummary(
        invoice_count=int(invoice_count or 0),
        approved_count=int(approved_count or 0),
        rejected_count=int(rejected_count or 0),
        pending_review_count=int(pending_review_count or 0),
        draft_count=int(draft_count or 0),
        approved_total=float(approved_total or 0.0),
        billed_total=float(billed_total or 0.0),
        variance_total=float(variance_total or 0.0),
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
            OrderTaxLine.tax_name.label("tax_name"),
            OrderTaxLine.tax_rate.label("tax_rate"),
            func.coalesce(func.sum(OrderTaxLine.taxable_base), 0.0).label(
                "total_taxable_base"
            ),
            func.coalesce(func.sum(OrderTaxLine.tax_amount), 0.0).label(
                "total_tax_amount"
            ),
            func.count(func.distinct(OrderTaxLine.order_id)).label("order_count"),
        )
        .join(Order, Order.id == OrderTaxLine.order_id)
        .filter(Order.status == "completed")
    )
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    rows = (
        query.group_by(OrderTaxLine.tax_name, OrderTaxLine.tax_rate)
        .order_by(func.sum(OrderTaxLine.tax_amount).desc())
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
