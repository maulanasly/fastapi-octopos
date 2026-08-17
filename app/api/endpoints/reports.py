from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.models.drawer import DrawerSession
from app.models.order import Order
from app.models.tax import OrderTaxLine as OrderTaxLineModel
from app.models.user import User
from app.schemas.product import Product as ProductSchema
from app.schemas.purchase import PurchaseInvoiceSummary
from app.schemas.report import (
    CategorySalesItem,
    DailyClose,
    DailyShiftItem,
    SalesSummary,
    ShiftReport,
    TopCustomerItem,
    TopProductItem,
)
from app.schemas.tax import TaxLiabilityItem, TaxLiabilitySummary
from app.services.reports import (
    get_category_sales_data,
    get_daily_close_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_shift_list_data,
    get_shift_report_data,
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
            tenant_id=current_user.tenant_id,
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
        tenant_id=current_user.tenant_id,
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
        tenant_id=current_user.tenant_id,
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
    return get_low_stock_products_data(
        db=db, threshold=threshold, tenant_id=current_user.tenant_id
    )


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
        tenant_id=current_user.tenant_id,
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
            tenant_id=current_user.tenant_id,
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
        .filter(
            Order.status == "completed",
            Order.tenant_id == current_user.tenant_id,
        )
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


@router.get("/shift/{reconciliation_id}", response_model=ShiftReport)
def get_shift_report(
    reconciliation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reports:view")),
):
    """Z-report for one closed drawer shift."""
    data = get_shift_report_data(
        db=db, reconciliation_id=reconciliation_id, tenant_id=current_user.tenant_id
    )
    if data is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Reconciliation not found")
    rec = data["reconciliation"]
    drawer = data["drawer"]
    return ShiftReport(
        reconciliation_id=rec.id,
        drawer_session_id=rec.drawer_session_id,
        opened_at=drawer.opened_at if drawer else None,
        closed_at=drawer.closed_at if drawer else None,
        operator_name=data["operator_name"],
        closed_by_name=data["closed_by_name"],
        starting_cash=float(drawer.starting_cash or 0.0) if drawer else 0.0,
        expected_cash=float(rec.expected_cash or 0.0),
        counted_cash=float(rec.counted_cash or 0.0),
        cash_variance=float(rec.cash_variance or 0.0),
        expected_non_cash=float(rec.expected_non_cash or 0.0),
        counted_non_cash=float(rec.counted_non_cash or 0.0),
        non_cash_variance=float(rec.non_cash_variance or 0.0),
        cash_sales_total=float(rec.cash_sales_total or 0.0),
        non_cash_sales_total=float(rec.non_cash_sales_total or 0.0),
        refunds_total=float(rec.refunds_total or 0.0),
        gross_sales_total=float(rec.gross_sales_total or 0.0),
        net_sales_total=float(rec.net_sales_total or 0.0),
        completed_order_count=int(rec.completed_order_count or 0),
        payment_breakdown=data["payment_breakdown"],
    )


@router.get("/shifts", response_model=List[DailyShiftItem])
def get_shift_list(
    db: Session = Depends(get_db),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permissions("reports:view")),
):
    """Recent reconciled shifts (newest first)."""
    return get_shift_list_data(
        db=db,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
        tenant_id=current_user.tenant_id,
    )


@router.get("/daily-close", response_model=DailyClose)
def get_daily_close(
    db: Session = Depends(get_db),
    report_date: Optional[datetime] = Query(
        None, description="ISO date (defaults to today)"
    ),
    current_user: User = Depends(require_permissions("reports:view")),
):
    """End-of-day report: every shift closed on the given day + totals."""
    data = get_daily_close_data(
        db=db, report_date=report_date, tenant_id=current_user.tenant_id
    )
    shifts = []
    for rec in data["shifts"]:
        drawer = (
            db.query(DrawerSession)
            .filter(
                DrawerSession.id == rec.drawer_session_id,
                DrawerSession.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        shifts.append(
            {
                "reconciliation_id": rec.id,
                "drawer_session_id": rec.drawer_session_id,
                "opened_at": drawer.opened_at if drawer else None,
                "closed_at": drawer.closed_at if drawer else None,
                "operator_name": drawer.user.full_name
                if drawer and drawer.user
                else None,
                "cash_sales_total": float(rec.cash_sales_total or 0.0),
                "non_cash_sales_total": float(rec.non_cash_sales_total or 0.0),
                "refunds_total": float(rec.refunds_total or 0.0),
                "gross_sales_total": float(rec.gross_sales_total or 0.0),
                "net_sales_total": float(rec.net_sales_total or 0.0),
                "completed_order_count": int(rec.completed_order_count or 0),
                "cash_variance": float(rec.cash_variance or 0.0),
            }
        )
    return DailyClose(date=data["date"], totals=data["totals"], shifts=shifts)
