import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import grpc

# --- 绝对导入各API路由模块 ---
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.embedding import router as embedding_router
import app.protos.inference_pb2_grpc as inference_pb2_grpc

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(
    title="Knowledge Base Backend API",
    description="API for interacting with the knowledge base and language models.",
    version="1.0.0"
)

# 全局 CORS 设置（允许所有源，开发环境推荐，生产可限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """应用启动时，建立到 gRPC 推理服务的连接。"""
    logger.info("应用启动，开始连接 gRPC 服务...")
    try:
        grpc_server_address = os.getenv("GRPC_SERVER_ADDRESS", "inference:50051")
        logger.info(f"正在连接到 gRPC 服务器: {grpc_server_address}")
        # 异步 gRPC 通道
        channel = grpc.aio.insecure_channel(grpc_server_address)
        app.state.grpc_client = inference_pb2_grpc.InferenceServiceStub(channel)
        logger.info("gRPC 客户端存根已创建。后续请求将使用此连接。")
    except Exception as e:
        logger.error(f"创建 gRPC 客户端时发生致命错误: {e}", exc_info=True)
        app.state.grpc_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时，执行清理操作。"""
    logger.info("应用关闭。")
    # FastAPI 会自动清理后台任务和连接

# 注册各 API 路由
app.include_router(admin_router,    prefix="/api/admin",    tags=["admin"])
app.include_router(chat_router,     prefix="/api/chat",     tags=["chat"])
app.include_router(embedding_router, prefix="/api/embedding", tags=["embedding"])

@app.get("/")
def read_root():
    """根路径健康检查。"""
    return {"message": "知识库后端服务已成功启动！"}
