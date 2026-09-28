from fastapi import APIRouter
from app.core.config import settings
from app.services.llm_response_service import get_gemini_model

router = APIRouter()


@router.get("/health", summary="Backend Health Check")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
        "llm_provider": settings.LLM_PROVIDER,
        "gemini_model": get_gemini_model()
    }


@router.get("/config/model", summary="Active LLM Model Information")
def get_model_info():
    """Safe read-only configuration endpoint returning strictly the configured model identifier."""
    return {
        "provider": settings.LLM_PROVIDER,
        "model": get_gemini_model()
    }

