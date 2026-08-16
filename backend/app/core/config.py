from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "RAGOps"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://ragops:ragops@localhost:5432/ragops"
    database_sync_url: str = "postgresql://ragops:ragops@localhost:5432/ragops"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_grpc_port: int = 6334

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "ragops"
    s3_region: str = "us-east-1"

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "ragops-backend"

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
