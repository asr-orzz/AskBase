from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "RAGOps"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://ragops:ragops@localhost:5432/ragops"
    database_sync_url: str = "postgresql://ragops:ragops@localhost:5432/ragops"

    @computed_field
    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.is_production and "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url += f"{sep}ssl=require"
        return url

    @computed_field
    @property
    def sync_database_url(self) -> str:
        url = self.database_sync_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if self.is_production and "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url += f"{sep}sslmode=require"
        return url
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_grpc_port: int = 6334
    qdrant_url: str = ""

    # LLM Providers
    openai_api_key: str = ""
    google_api_key: str = ""

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
