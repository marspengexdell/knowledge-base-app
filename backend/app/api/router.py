from fastapi import APIRouter

# Import the router objects from our endpoint files
from .endpoints import chat, admin

# Create the main API router
api_router = APIRouter()

# Include the routers from the endpoint modules.
# All routes from chat.py will be prefixed with /chat.
# All routes from admin.py will be prefixed with /admin.
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
