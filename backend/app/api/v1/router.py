from fastapi import APIRouter

from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.query import router as query_router
from app.api.v1.documents import router as docs_router
from app.api.v1.sync import router as sync_router
from app.api.v1.evaluations import router as eval_router
from app.api.v1.experiments import router as experiment_router
from app.api.v1.observability import router as obs_router

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ragops-api",
        "version": "0.1.0",
    }


router.include_router(kb_router)
router.include_router(query_router)
router.include_router(docs_router)
router.include_router(sync_router)
router.include_router(eval_router)
router.include_router(experiment_router)
router.include_router(obs_router)
