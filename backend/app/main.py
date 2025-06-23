import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import grpc

# --- 关键修正：使用正确的绝对导入路径 ---
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.chat import router as chat_router
# gRPC 文件现在位于 app 包内，可以直接导入
import app.protos.inference_pb2_grpc as inference_pb2_grpc

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(
    title="Knowledge Base Backend API",
    description="API for interacting with the knowledge base and language models.",
    version="1.0.0"
)

# CORS 中间件，允许所有跨域请求
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
        # 从环境变量读取 gRPC 服务器地址，这是容器间通信的关键
        grpc_server_address = os.getenv("GRPC_SERVER_ADDRESS", "inference:50051")
        logger.info(f"正在连接到 gRPC 服务器: {grpc_server_address}")
        
        # 建立一个异步 gRPC 通道
        channel = grpc.aio.insecure_channel(grpc_server_address)
        
        # 将客户端存根附加到 app state，以便在整个应用中共享和访问
        app.state.grpc_client = inference_pb2_grpc.InferenceServiceStub(channel)
        
        logger.info("gRPC 客户端存根已创建。后续请求将使用此连接。")

    except Exception as e:
        logger.error(f"创建 gRPC 客户端时发生致命错误: {e}", exc_info=True)
        app.state.grpc_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时，执行清理操作。"""
    logger.info("应用关闭。")
    # FastAPI 会自动处理后台任务和连接的关闭

# 包含 API 路由
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

@app.get("/")
def read_root():
    """根路径，用于简单的健康检查。"""
    return {"message": "知识库后端服务已成功启动！"}