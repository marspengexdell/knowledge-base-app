import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.chat import router as chat_router
from app.core.grpc_client import grpc_client_manager

# Add protos directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "protos"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Base API",
    description="API for interacting with the knowledge base and language models.",
    version="1.0.0"
)

# CORS Middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API routers
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"]) # Correctly prefixed

@app.on_event("startup")
async def startup_event():
    """
    Application startup event: connect the gRPC client.
    """
    logger.info("Application startup...")
    try:
        await grpc_client_manager.connect()
        logger.info("gRPC client connected successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to gRPC server on startup: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event: disconnect the gRPC client.
    """
    logger.info("Application shutdown...")
    await grpc_client_manager.disconnect()
    logger.info("gRPC client disconnected.")

@app.get("/")
def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Knowledge Base App"}