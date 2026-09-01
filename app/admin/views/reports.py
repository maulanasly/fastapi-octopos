from datetime import UTC, datetime, timedelta

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, expose
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.base import REPORTS_CACHE_SECONDS, _reports_cache, _selected_tenant_id
from app.core.database import SessionLocal
from app.core.localization import format_currency, get_localization_setting
from app.models.shift_reconciliation import ShiftReconciliation
from app.services.reports import (
    get_category_sales_data,
    get_executive_summary_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_supplier_payment_summary_data,
    get_top_customers_data,
    get_top_products_data,
)


class ReportsAdmin(BaseView):
    name = "Reports Dashboard"
    icon = "fa-solid fa-chart-line"
    category = "Reports"
    category_icon = "fa-solid fa-chart-pie"

    def _period_range(self, now: datetime, period: str) -> tuple:
        if period == "today":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=UTC,
            )
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "month":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=1,
                tzinfo=UTC,
            )
        else:
            start_date = None
        return start_date, None

    def _build_report_data(self, db, period: str, localization) -> dict:
        now = datetime.now(UTC)
        if period not in ("today", "7d", "30d", "month"):
            period = "all"
        start_date, end_date = self._period_range(now, period)

        sales_summary = get_sales_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        top_products = get_top_products_data(
            db=db, start_date=start_date, end_date=end_date, limit=10
        )
        category_sales = get_category_sales_data(
            db=db, start_date=start_date, end_date=end_date
        )
        low_stock_products = get_low_stock_products_data(db=db)
        top_customers = get_top_customers_data(
            db=db, start_date=start_date, end_date=end_date, limit=5
        )
        invoice_summary = get_invoice_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        payment_summary = get_supplier_payment_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        executive_summary = get_executive_summary_data(
            db=db, invoice_summary=invoice_summary
        )

        localized = {
            "net_revenue": format_currency(
                float(sales_summary["net_revenue"]),
                localization.currency,
                localization.number_format,
            ),
            "total_refunds": format_currency(
                float(sales_summary["total_refunds"]),
                localization.currency,
                localization.number_format,
            ),
            "average_order_value": format_currency(
                float(sales_summary["average_order_value"]),
                localization.currency,
                localization.number_format,
            ),
            "gross_revenue": format_currency(
                float(sales_summary["gross_revenue"]),
                localization.currency,
                localization.number_format,
            ),
            "total_discounts": format_currency(
                float(sales_summary["total_discounts"]),
                localization.currency,
                localization.number_format,
            ),
            "purchase_received_value": format_currency(
                float(executive_summary["purchase_received_value"]),
                localization.currency,
                localization.number_format,
            ),
            "average_cash_variance": format_currency(
                float(executive_summary["average_cash_variance"]),
                localization.currency,
                localization.number_format,
            ),
            "invoice_approved_total": format_currency(
                float(executive_summary["invoice_approved_total"]),
                localization.currency,
                localization.number_format,
            ),
            "invoice_variance_total": format_currency(
                float(executive_summary["invoice_variance_total"]),
                localization.currency,
                localization.number_format,
            ),
            "supplier_paid_total": format_currency(
                float(payment_summary["approved_total"]),
                localization.currency,
                localization.number_format,
            ),
            "supplier_outstanding": format_currency(
                float(payment_summary["outstanding_payable"]),
                localization.currency,
                localization.number_format,
            ),
        }

        top_products_view = [
            {
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in top_products
        ]
        category_sales_view = [
            {
                "category_name": row.category_name,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in category_sales
        ]
        top_customers_view = [
            {
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "order_count": row.order_count,
                "total_spent": row.total_spent,
                "total_spent_formatted": format_currency(
                    float(row.total_spent or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
                "points_balance": row.points_balance,
            }
            for row in top_customers
        ]

        return {
            "period_label": {
                "today": "Today",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "month": "This Month",
                "all": "All Time",
            }[period],
            "localized": localized,
            "sales_summary": sales_summary,
            "top_products": top_products_view,
            "category_sales": category_sales_view,
            "low_stock_products": low_stock_products,
            "top_customers": top_customers_view,
            "executive_summary": executive_summary,
        }

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            localization = get_localization_setting(db, _selected_tenant_id(request))
            period = request.query_params.get("period", "30d")

            shift_reports = (
                db.query(ShiftReconciliation)
                .options(
                    joinedload(ShiftReconciliation.drawer_session),
                    joinedload(ShiftReconciliation.closed_by_user),
                )
                .order_by(ShiftReconciliation.id.desc())
                .limit(10)
                .all()
            )

            cache_key = (period, localization.currency, localization.number_format)
            cached = _reports_cache.get(cache_key)
            now = datetime.now(UTC).timestamp()
            if cached and now - cached[0] < REPORTS_CACHE_SECONDS:
                data = cached[1]
            else:
                data = self._build_report_data(db, period, localization)
                _reports_cache[cache_key] = (
                    now,
                    {
                        k: (v.copy() if isinstance(v, dict) else v)
                        for k, v in data.items()
                    },
                )

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "period": period,
                    "period_label": data["period_label"],
                    "localization": localization,
                    "localized": data["localized"],
                    "sales_summary": data["sales_summary"],
                    "top_products": data["top_products"],
                    "category_sales": data["category_sales"],
                    "low_stock_products": data["low_stock_products"],
                    "top_customers": data["top_customers"],
                    "executive_summary": data["executive_summary"],
                    "shift_reports": shift_reports,
                },
            )
        finally:
            db.close()

    @expose("/reports/shift/{reconciliation_id}/print", methods=["GET"])
    async def shift_report_print_page(self, request: Request, reconciliation_id: int):
        """Print-friendly Z-report for a closed drawer shift (admin session)."""
        from datetime import datetime as _dt

        from app.services.reports import get_shift_report_data

        db = SessionLocal()
        try:
            data = get_shift_report_data(db=db, reconciliation_id=reconciliation_id)
            if data is None:
                raise HTTPException(status_code=404)
            rec = data["reconciliation"]
            drawer = data["drawer"]
            report = {
                "reconciliation_id": rec.id,
                "drawer_session_id": rec.drawer_session_id,
                "opened_at": drawer.opened_at if drawer else None,
                "closed_at": drawer.closed_at if drawer else None,
                "operator_name": data["operator_name"],
                "closed_by_name": data["closed_by_name"],
                "starting_cash": float(drawer.starting_cash or 0.0) if drawer else 0.0,
                "expected_cash": float(rec.expected_cash or 0.0),
                "counted_cash": float(rec.counted_cash or 0.0),
                "cash_variance": float(rec.cash_variance or 0.0),
                "expected_non_cash": float(rec.expected_non_cash or 0.0),
                "counted_non_cash": float(rec.counted_non_cash or 0.0),
                "non_cash_variance": float(rec.non_cash_variance or 0.0),
                "cash_sales_total": float(rec.cash_sales_total or 0.0),
                "non_cash_sales_total": float(rec.non_cash_sales_total or 0.0),
                "refunds_total": float(rec.refunds_total or 0.0),
                "gross_sales_total": float(rec.gross_sales_total or 0.0),
                "net_sales_total": float(rec.net_sales_total or 0.0),
                "completed_order_count": int(rec.completed_order_count or 0),
                "payment_breakdown": data["payment_breakdown"],
            }
            return await self.templates.TemplateResponse(
                request,
                "report_shift.html",
                context={
                    "report": report,
                    "now": _dt.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                    "title": f"Shift Report #{rec.id}",
                },
            )
        finally:
            db.close()
