from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ragops-api",
        "version": "0.1.0",
    }
