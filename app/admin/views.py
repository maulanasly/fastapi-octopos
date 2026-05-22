# pyrefly: ignore [missing-import]
from sqladmin import BaseView, ModelView, expose
from sqlalchemy import func

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.core.database import SessionLocal
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
    ]
    column_searchable_list = [User.email, User.full_name]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.description]
    column_searchable_list = [Category.name]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.price,
        Product.stock_quantity,
        Product.category,
    ]
    column_searchable_list = [Product.name, Product.sku]
    column_sortable_list = [Product.price, Product.stock_quantity]


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user,
        Order.total_amount,
        Order.status,
        Order.created_at,
    ]
    column_sortable_list = [Order.created_at, Order.total_amount]
    column_searchable_list = [Order.id]


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
    ]
    column_searchable_list = [OrderItem.order_id]


class DrawerSessionAdmin(ModelView, model=DrawerSession):
    column_list = [
        DrawerSession.id,
        DrawerSession.user,
        DrawerSession.opened_at,
        DrawerSession.closed_at,
        DrawerSession.starting_cash,
        DrawerSession.ending_cash,
        DrawerSession.status,
    ]
    column_searchable_list = [DrawerSession.status]
    column_sortable_list = [DrawerSession.opened_at, DrawerSession.closed_at]


class ReportsAdmin(BaseView):
    name = "Reports Dashboard"
    icon = "fa-solid fa-chart-line"

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            # 1. Sales Summary
            summary_query = db.query(
                func.coalesce(func.sum(Order.total_amount), 0.0),
                func.count(Order.id),
            ).filter(Order.status == "completed")
            total_revenue, order_count = summary_query.first()
            average_order_value = (
                total_revenue / order_count if order_count > 0 else 0.0
            )
            sales_summary = {
                "total_revenue": total_revenue,
                "order_count": order_count,
                "average_order_value": average_order_value,
            }

            # 2. Top Selling Products
            top_products_query = (
                db.query(
                    Product.id.label("product_id"),
                    Product.name.label("product_name"),
                    Product.sku.label("product_sku"),
                    func.sum(OrderItem.quantity).label("total_quantity_sold"),
                    func.sum(OrderItem.quantity * OrderItem.unit_price).label(
                        "total_revenue"
                    ),
                )
                .select_from(OrderItem)
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .filter(Order.status == "completed")
                .group_by(Product.id)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(10)
            )
            top_products = top_products_query.all()

            # 3. Sales by Category
            category_sales_query = (
                db.query(
                    Category.id.label("category_id"),
                    func.coalesce(Category.name, "Uncategorized").label(
                        "category_name"
                    ),
                    func.sum(OrderItem.quantity).label("total_quantity_sold"),
                    func.sum(OrderItem.quantity * OrderItem.unit_price).label(
                        "total_revenue"
                    ),
                )
                .select_from(OrderItem)
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .outerjoin(Category, Product.category_id == Category.id)
                .filter(Order.status == "completed")
                .group_by(Category.id, Category.name)
                .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            )
            category_sales = category_sales_query.all()

            # 4. Low Stock Products (threshold <= 10)
            low_stock_products = (
                db.query(Product).filter(Product.stock_quantity <= 10).all()
            )

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "sales_summary": sales_summary,
                    "top_products": top_products,
                    "category_sales": category_sales,
                    "low_stock_products": low_stock_products,
                },
            )
        finally:
            db.close()
