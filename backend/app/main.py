import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), 'protos'))

from .api.router import api_router
from .core.config import settings
from .core.grpc_client import grpc_client_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Server for the Knowledge Base App, handling chat and admin operations.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logging.info("Application startup...")
    await grpc_client_manager.connect()
    logging.info("gRPC client connected.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown...")
    await grpc_client_manager.disconnect()
    logging.info("gRPC client disconnected.")

app.include_router(api_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}
