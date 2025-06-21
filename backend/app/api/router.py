from fastapi import APIRouter
from .endpoints import chat, admin

api_router = APIRouter()

# 路由前缀/prefix不要再加/api了，由main.py加
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
