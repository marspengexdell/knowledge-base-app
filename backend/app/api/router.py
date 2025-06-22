from fastapi import APIRouter
from .endpoints import chat, admin, knowledge

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(knowledge.router, prefix="/admin/knowledge", tags=["Knowledge"])
