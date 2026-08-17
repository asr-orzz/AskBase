from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.query import router as query_router
from app.api.v1.documents import router as docs_router

router = APIRouter()


@router.get("/health")
async def health_check():
    checks = {"service": "ragops-api", "version": "0.1.0"}

    try:
        from sqlalchemy import text
        from app.core.database import async_session_factory
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store()
        vs.client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {e}"

    checks["status"] = "healthy" if checks.get("database") == "ok" and checks.get("qdrant") == "ok" else "degraded"
    return checks


router.include_router(auth_router)
router.include_router(kb_router)
router.include_router(query_router)
router.include_router(docs_router)
