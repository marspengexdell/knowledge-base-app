from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from .api.endpoints.chat import router as chat_router
from .api.endpoints.admin import router as admin_router
from .api.endpoints.embedding import router as embedding_router
from .core.grpc_client import grpc_client_manager
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Knowledge Base API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("尝试连接到 gRPC 服务")
    for i in range(10):
        try:
            await grpc_client_manager.connect()
            logger.info("连接成功")
            return
        except Exception as e:
            logger.warning(f"第{i+1}次重试失败：{e}，等待5秒")
            await asyncio.sleep(5)
    logger.error("未能连接 gRPC 服务，AI相关功能将不可用")

@app.on_event("shutdown")
async def shutdown_event():
    await grpc_client_manager.disconnect()

app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(embedding_router, prefix="/api/embedding", tags=["Embedding"])

@app.get("/")
def read_root():
    return {"message": "后端启动成功！"}
