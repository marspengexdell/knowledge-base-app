from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.admin import admin_router
from app.api.endpoints.chat import chat_router
from app.services.chat_service import ConnectionManager
from app.core.config import settings
import grpc
from app.protos import inference_pb2_grpc
import logging
import os # 引入 os 模块

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS 中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理器
manager = ConnectionManager()

# 包含其他路由
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行的事件
    """
    logger.info("Application startup...")
    try:
        # --- 这是关键修改 ---
        # 从环境变量中读取 gRPC 服务器地址
        grpc_server_address = os.getenv("GRPC_SERVER_ADDRESS", "localhost:50051")
        logger.info(f"Connecting to gRPC server at: {grpc_server_address}")
        
        # 使用配置的地址建立 gRPC 连接
        channel = grpc.aio.insecure_channel(grpc_server_address)
        app.state.grpc_client = inference_pb2_grpc.InferenceServiceStub(channel)
        
        # 检查连接
        await channel.channel_ready()
        logger.info("gRPC client connected.")

    except Exception as e:
        logger.error(f"Failed to connect to gRPC server: {e}", exc_info=True)
        app.state.grpc_client = None

@app.websocket("/api/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    处理 WebSocket 连接
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 在这里可以处理接收到的消息，例如广播给其他客户端
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #... says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected: {websocket.client}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Knowledge Base App"}