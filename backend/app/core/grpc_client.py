import grpc
import logging
import os
import sys
from typing import Optional

# --- Add protos to Python path ---
proto_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos'))
if proto_path not in sys.path:
    sys.path.insert(0, proto_path)

import inference_pb2
import inference_pb2_grpc

class GrpcClientManager:
    """
    异步gRPC管理器，支持FastAPI/WebSocket异步流式API。
    """
    def __init__(self):
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[inference_pb2_grpc.InferenceServiceStub] = None
        self.server_url = os.getenv("INFERENCE_SERVER_URL", os.getenv("GRPC_SERVER", "inference:50051"))
        logging.info(f"gRPC client will connect to: {self.server_url}")

    async def connect(self):
        """启动时主动连接gRPC服务"""
        if not self.channel:
            logging.info(f"Connecting to gRPC server at {self.server_url} ...")
            self.channel = grpc.aio.insecure_channel(self.server_url)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            logging.info("gRPC async channel and stub created.")

    async def disconnect(self):
        """关闭gRPC连接"""
        if self.channel:
            logging.info("Closing gRPC async channel.")
            await self.channel.close()
            self.channel = None
            self.stub = None
            logging.info("gRPC channel closed.")

    async def get_stub(self) -> inference_pb2_grpc.InferenceServiceStub:
        """获取gRPC异步stub，如果没连接自动连接一次"""
        if not self.stub:
            await self.connect()
        return self.stub

grpc_client_manager = GrpcClientManager()
