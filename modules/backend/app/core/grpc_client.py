import grpc
from protos import inference_pb2
from protos import inference_pb2_grpc
from core.settings import settings
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class GrpcClientManager:
    def __init__(self):
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[inference_pb2_grpc.InferenceServiceStub] = None

    async def connect(self):
        """连接到 gRPC 推理服务。settings.GRPC_SERVER 建议配置为 'inference:50051'。"""
        try:
            self.channel = grpc.aio.insecure_channel(settings.GRPC_SERVER)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            await self.channel.channel_ready()
            logger.info(f"Connected to gRPC server at {settings.GRPC_SERVER}")
        except Exception as e:
            logger.error(f"Failed to connect gRPC server at {settings.GRPC_SERVER}: {e}")
            raise

    async def disconnect(self):
        """断开 gRPC 连接。"""
        if self.channel:
            await self.channel.close()
        self.stub = None
        self.channel = None
        logger.info("Disconnected from gRPC server")

    async def chat(self, req: inference_pb2.ChatRequest):
        """Stream chat completions from the inference server."""
        if not self.stub:
            yield "[Error: no connection]"
            return
        try:
            async for resp in self.stub.ChatStream(req):
                if resp.HasField("token"):
                    yield resp.token
                else:
                    yield f"[Error: {resp.error_message}]"
        except Exception as e:
            logger.error(f"gRPC chat error: {e}")
            yield f"[Error: {e}]"

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.stub:
            raise ConnectionError("gRPC not connected")
        if not texts:
            return []
        req = inference_pb2.EmbeddingBatchRequest(texts=texts)
        resp = await self.stub.GetEmbeddingsBatch(req)
        return [list(e.values) for e in resp.embeddings]

    async def list_models(self):
        if not self.stub:
            raise ConnectionError("gRPC not connected")
        req = inference_pb2.Empty()
        resp = await self.stub.ListAvailableModels(req)
        return {
            "generation_models": list(resp.generation_models),
            "embedding_models": list(resp.embedding_models),
            "current_generation_model": resp.current_generation_model,
            "current_embedding_model": resp.current_embedding_model,
            "device": getattr(resp, "device", ""),
        }

    async def switch_model(self, model_name: str, model_type_enum):
        if not self.stub:
            raise ConnectionError("gRPC not connected")
        req = inference_pb2.SwitchModelRequest(
            model_name=model_name, model_type=model_type_enum
        )
        resp = await self.stub.SwitchModel(req)
        return resp.success, resp.message

grpc_client_manager = GrpcClientManager()
