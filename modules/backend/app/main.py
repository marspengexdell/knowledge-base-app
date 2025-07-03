from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.router import api_router   # 用统一路由聚合器更整洁

import logging
import asyncio

from core.grpc_client import grpc_client_manager

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

# 统一路由前缀
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "后端启动成功！"}
def SwitchModel(self, request, context):
    logger.info(f"收到 SwitchModel 请求: {request.model_name}")
    res = model_manager.switch_model(request.model_name)
    logger.info(f"SwitchModel 响应: {res}")
    return inference_pb2.SwitchModelResponse(
        success=res["status"] in ("loading_started", "already_loaded"),
        message=res.get("message", ""),
    )
