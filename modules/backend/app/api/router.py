from fastapi import APIRouter
from api.endpoints import chat, models, kb_admin

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(models.router, prefix="/admin/models", tags=["Models"])
api_router.include_router(kb_admin.router, prefix="/admin/kb", tags=["KnowledgeBaseAdmin"])
