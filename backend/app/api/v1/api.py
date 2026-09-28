from fastapi import APIRouter
from app.api.v1 import health, chat, coaching, analytics, admin, auth

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & Coaching"])
api_router.include_router(coaching.router, prefix="/coaching", tags=["Coaching Feedback"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Management"])
