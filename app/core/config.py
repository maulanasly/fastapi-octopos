from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI POS Backend"
    API_V1_STR: str = "/api/v1"

    # CORS — set explicit origins in production (e.g. ["https://yourapp.com"])
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Database
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sql_app.db"

    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Should be random string in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Google Auth
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
