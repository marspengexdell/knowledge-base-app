import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Add protos to Python path ---
# This allows us to import the generated gRPC files from the 'protos' directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'protos'))

# --- Local Imports ---
# Import the components we've built
from .api.router import api_router
from .core.config import settings
from .core.grpc_client import grpc_client_manager

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI App Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Server for the Knowledge Base App, handling chat and admin operations.",
    version="0.1.0"
)

# --- CORS Middleware ---
# Use the origins defined in our settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Application Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Connect to the gRPC server.
    """
    logging.info("Application startup...")
    # Establish the connection to the inference service
    await grpc_client_manager.connect()
    logging.info("gRPC client connected.")
    

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    - Disconnect the gRPC client.
    """
    logging.info("Application shutdown...")
    # Gracefully close the connection to the inference service
    await grpc_client_manager.disconnect()
    logging.info("gRPC client disconnected.")


# --- Include API Routers ---
# Mount the main API router, which includes both chat and admin endpoints.
# All routes will be available under the /api prefix.
app.include_router(api_router, prefix="/api")


# --- Root Endpoint ---
@app.get("/")
async def read_root():
    """
    A simple endpoint to check if the server is running.
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}

# Note: The placeholder WebSocket endpoint has been removed from here
# as the real implementation is now handled by the chat router.
