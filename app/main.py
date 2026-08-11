# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# pyrefly: ignore [missing-import]
from sqladmin import Admin

# pyrefly: ignore [missing-import]
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# pyrefly: ignore [missing-import]
from starlette.middleware.sessions import SessionMiddleware

from app.admin import all_admin_views
from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter

settings.fail_closed()

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource conflict or duplicate entry"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal database error"},
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

for admin_view in all_admin_views:
    admin.add_view(admin_view)


@app.get("/")
def root():
    return {
        "message": "Welcome to FastAPI POS Backend",
        "docs": "/docs",
        "admin": "/admin",
    }
