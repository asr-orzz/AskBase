from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    settings = get_settings()
    await logger.ainfo(
        "Starting RAGOps",
        env=settings.app_env,
        debug=settings.debug,
    )
    yield
    await logger.ainfo("Shutting down RAGOps")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Production platform for building, deploying, evaluating, and operating RAG applications",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


app = create_app()
