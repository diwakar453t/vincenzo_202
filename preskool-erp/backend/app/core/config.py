from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PreSkool ERP"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./preskool.db"
    sync_database_url: str = "sqlite:///./preskool.db"
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    default_tenant_id: str = "default"
    superadmin_email: str = "admin@preskool.com"
    superadmin_password: str = "Admin@1234"
    superadmin_name: str = "Super Admin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
