from pathlib import Path
from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI POS Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | production

    # CORS — set explicit origins in production (e.g. ["https://yourapp.com"])
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:8080"]
    # Optional regex of additional origins. Set to a localhost pattern for
    # dev clients on ephemeral ports (e.g. `flutter run -d chrome`).
    BACKEND_CORS_ORIGIN_REGEX: str = ""

    # Database
    SQLALCHEMY_DATABASE_URI: str = (
        f"sqlite:///{(Path(__file__).resolve().parents[2] / 'sql_app.db').as_posix()}"
    )

    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Should be random string in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Google Auth
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_SESSION_HOURS: int = 12

    # Order reservation
    ORDER_RESERVATION_TIMEOUT_MINUTES: int = 15
    RESERVATION_AUTO_EXPIRE_ENABLED: bool = False
    RESERVATION_AUTO_EXPIRE_INTERVAL_SECONDS: int = 300

    # Tax
    # Rate for the migration-seeded default tax rule (0 keeps new installs tax-free
    # until an operator configures rules; set per jurisdiction, e.g. 7.25).
    DEFAULT_TAX_RATE: float = 0.0
    DEFAULT_TAX_NAME: str = "VAT"

    # Login lockout
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Product images
    MEDIA_DIR: str = "media"

    # Auto purchase orders
    REPLENISHMENT_AUTO_PO_ENABLED: bool = False
    REPLENISHMENT_CHECK_INTERVAL_SECONDS: int = 3600
    REPLENISHMENT_LOOKBACK_DAYS: int = 30

    # Rate limiting — storage URI for slowapi. Empty = in-memory (single
    # process only); set e.g. "redis://localhost:6380" for multi-worker
    # deployments so limits are shared across processes.
    RATE_LIMIT_STORAGE_URI: str = ""

    # Semantic search embeddings (products)
    # "hash" (default, offline) | "api" (OpenAI-compatible /embeddings) | "none"
    EMBEDDING_PROVIDER: str = "hash"
    EMBEDDING_MODEL: str = "all-minilm"
    EMBEDDING_DIM: int = 384  # must match the products.embedding column
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    def fail_closed(self) -> None:
        """Refuse to run with default/dummy credentials in production."""
        if self.ENVIRONMENT != "production":
            return
        insecure = []
        if self.SECRET_KEY in {
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        }:
            insecure.append("SECRET_KEY is the FastAPI tutorial default")
        if self.ADMIN_PASSWORD == "admin":
            insecure.append("ADMIN_PASSWORD is the default 'admin'")
        if self.ORDER_RESERVATION_TIMEOUT_MINUTES > 0 and not (
            self.RESERVATION_AUTO_EXPIRE_ENABLED
        ):
            insecure.append(
                "RESERVATION_AUTO_EXPIRE_ENABLED is off but orders reserve stock"
            )
        if insecure:
            raise RuntimeError(
                "Refusing to start in production mode: " + "; ".join(insecure)
            )


settings = Settings()
