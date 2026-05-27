# pyrefly: ignore [missing-import]
from fastapi import FastAPI

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# pyrefly: ignore [missing-import]
from sqladmin import Admin

# pyrefly: ignore [missing-import]
from sqladmin.authentication import AuthenticationBackend

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.views import (
    CategoryAdmin,
    CustomerAdmin,
    DrawerSessionAdmin,
    LocalizationSettingAdmin,
    LoyaltyTransactionAdmin,
    OrderAdmin,
    OrderItemAdmin,
    ProductAdmin,
    PromotionAdmin,
    PurchaseInvoiceAdmin,
    PurchaseInvoiceItemAdmin,
    PurchaseOrderAdmin,
    PurchaseOrderItemAdmin,
    RefundAdmin,
    RefundItemAdmin,
    ReportsAdmin,
    ShiftReconciliationAdmin,
    StockMovementAdmin,
    SupplierAdmin,
    SyncEventLogAdmin,
    UserAdmin,
)
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.limiter import limiter

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


# Setup SQLAdmin Authentication
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Super simple hardcoded admin auth for development
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": "admin-token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
admin = Admin(
    app=app,
    engine=engine,
    templates_dir="app/templates",
    authentication_backend=authentication_backend,
)

admin.add_view(UserAdmin)
admin.add_view(LocalizationSettingAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(CustomerAdmin)
admin.add_view(LoyaltyTransactionAdmin)
admin.add_view(ProductAdmin)
admin.add_view(PromotionAdmin)
admin.add_view(SupplierAdmin)
admin.add_view(PurchaseOrderAdmin)
admin.add_view(PurchaseOrderItemAdmin)
admin.add_view(PurchaseInvoiceAdmin)
admin.add_view(PurchaseInvoiceItemAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)
admin.add_view(RefundAdmin)
admin.add_view(RefundItemAdmin)
admin.add_view(ShiftReconciliationAdmin)
admin.add_view(StockMovementAdmin)
admin.add_view(SyncEventLogAdmin)
admin.add_view(ReportsAdmin)
admin.add_view(DrawerSessionAdmin)


@app.get("/")
def root():
    return {
        "message": "Welcome to FastAPI POS Backend",
        "docs": "/docs",
        "admin": "/admin",
    }
