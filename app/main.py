# pyrefly: ignore [missing-import]
import asyncio
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
from app.core.database import SessionLocal, engine
from app.core.limiter import limiter
from app.core.media import CachedStaticFiles, SkipMediaGZipMiddleware
from app.core.observability import RequestIDMiddleware, setup_logging
from app.core.security import verify_password

settings.fail_closed()
setup_logging()


async def _reservation_expiry_loop() -> None:
    """Periodically release expired order reservations in the background."""
    from app.core.exclusive_task import RESERVATION_SWEEP_LOCK, run_exclusive

    while True:
        await asyncio.sleep(settings.RESERVATION_AUTO_EXPIRE_INTERVAL_SECONDS)
        await asyncio.to_thread(
            run_exclusive,
            engine,
            RESERVATION_SWEEP_LOCK,
            _release_expired_reservations_sync,
        )


def _auto_po_sync() -> None:
    from app.core.database import SessionLocal
    from app.services.auto_po import auto_generate_purchase_orders

    db = SessionLocal()
    try:
        auto_generate_purchase_orders(
            db=db, lookback_days=settings.REPLENISHMENT_LOOKBACK_DAYS
        )
        db.commit()
    finally:
        db.close()


async def _auto_po_loop() -> None:
    """Periodically generate draft purchase orders from reorder points."""
    from app.core.exclusive_task import AUTO_PO_LOCK, run_exclusive

    while True:
        await asyncio.sleep(settings.REPLENISHMENT_CHECK_INTERVAL_SECONDS)
        await asyncio.to_thread(run_exclusive, engine, AUTO_PO_LOCK, _auto_po_sync)


def _release_expired_reservations_sync() -> None:
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.orders import release_expired_reservations_for_user

    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.is_superuser.is_(True), User.is_active.is_(True))
            .order_by(User.id.asc())
            .first()
        )
        if user:
            release_expired_reservations_for_user(db=db, user_id=user.id)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = []
    if settings.RESERVATION_AUTO_EXPIRE_ENABLED:
        # One-shot sweep at startup catches reservations that expired while the
        # process was down, then the periodic loop keeps them fresh. Guarded so
        # only one worker of a multi-worker deployment runs it.
        from app.core.exclusive_task import RESERVATION_SWEEP_LOCK, run_exclusive

        await asyncio.to_thread(
            run_exclusive,
            engine,
            RESERVATION_SWEEP_LOCK,
            _release_expired_reservations_sync,
        )
        tasks.append(asyncio.create_task(_reservation_expiry_loop()))
    if settings.REPLENISHMENT_AUTO_PO_ENABLED:
        tasks.append(asyncio.create_task(_auto_po_loop()))
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
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
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SkipMediaGZipMiddleware, minimum_size=500)


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
    import logging

    logging.getLogger("app").exception(
        "Database error on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal database error"},
    )


app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve uploaded product images (public read for POS terminals).
_MEDIA_PATH = Path(settings.MEDIA_DIR).resolve()
_MEDIA_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/media", CachedStaticFiles(directory=str(_MEDIA_PATH)), name="media")


def _admin_session_expiry() -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.ADMIN_SESSION_HOURS)
    return expires.isoformat()


# Setup SQLAdmin Authentication
class AdminAuth(AuthenticationBackend):
    """Admin authentication backed by real application users.

    Credentials are verified against the :class:`User` table with the same
    password hashing as the API. Only active superusers may sign in.
    A plaintext ADMIN_USERNAME/ADMIN_PASSWORD fallback is honoured ONLY in
    non-production environments, to bootstrap the first admin account.
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        if settings.ENVIRONMENT != "production":
            if (username == settings.ADMIN_USERNAME) and (
                password == settings.ADMIN_PASSWORD
            ):
                request.session.update(
                    {
                        "admin_token": secrets.token_urlsafe(48),
                        "admin_expires_at": _admin_session_expiry(),
                    }
                )
                return True

        from app.models.user import User

        db = SessionLocal()
        try:
            user = (
                db.query(User)
                .filter(User.email == username, User.is_active.is_(True))
                .first()
            )
            if not user or not user.hashed_password:
                return False
            if not verify_password(password, user.hashed_password):
                return False
            if not user.is_superuser:
                return False
        finally:
            db.close()

        request.session.update(
            {
                "admin_token": secrets.token_urlsafe(48),
                "admin_user_id": user.id,
                "admin_expires_at": _admin_session_expiry(),
            }
        )
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("admin_token")
        if not token:
            return False

        expires_at = request.session.get("admin_expires_at")
        if not expires_at:
            return False
        try:
            expires_dt = datetime.fromisoformat(expires_at)
        except ValueError:
            return False
        if expires_dt <= datetime.now(timezone.utc):
            request.session.clear()
            return False

        if "admin_user_id" in request.session:
            from app.models.user import User

            db = SessionLocal()
            try:
                user = db.get(User, int(request.session["admin_user_id"]))
                if not user or not user.is_active or not user.is_superuser:
                    request.session.clear()
                    return False
            finally:
                db.close()
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
