from pathlib import Path
from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI POS Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | production

    # CORS — set explicit origins in production (e.g. ["https://yourapp.com"])
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

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

    # Order reservation
    ORDER_RESERVATION_TIMEOUT_MINUTES: int = 15

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

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
        if insecure:
            raise RuntimeError(
                "Refusing to start in production mode: " + "; ".join(insecure)
            )


settings = Settings()
