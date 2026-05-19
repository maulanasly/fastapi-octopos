# pyrefly: ignore [missing-import]
from fastapi import Depends, FastAPI

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]
from sqladmin import Admin

# pyrefly: ignore [missing-import]
from sqladmin.authentication import AuthenticationBackend

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.views import (
    CategoryAdmin,
    OrderAdmin,
    OrderItemAdmin,
    ProductAdmin,
    UserAdmin,
)
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import get_password_hash

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)


@app.get("/")
def root():
    return {
        "message": "Welcome to FastAPI POS Backend",
        "docs": "/docs",
        "admin": "/admin",
    }
