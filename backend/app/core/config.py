"""
Application settings loaded from environment variables / .env file.
Centralizing configuration here means no secrets or magic values are
scattered through the codebase.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://churn_user:churn_password@localhost:5432/churn_db"

    # Auth
    SECRET_KEY: str = "dev-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ML artifacts
    MODEL_PATH: str = "../ml/model/churn_model.pkl"
    METRICS_PATH: str = "../ml/model/metrics.json"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500"

    # Bootstrap admin
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"

    # Risk classification thresholds (configurable in ONE place, per spec)
    RISK_LOW_MAX: float = 0.39
    RISK_MEDIUM_MAX: float = 0.69

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def model_path_resolved(self) -> str:
        return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", self.MODEL_PATH))

    @property
    def metrics_path_resolved(self) -> str:
        return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", self.METRICS_PATH))


@lru_cache
def get_settings() -> Settings:
    return Settings()
