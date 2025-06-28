import grpc
from ..protos import inference_pb2, inference_pb2_grpc
from ..core.settings import settings
import logging
from typing import List

logger = logging.getLogger(__name__)

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        if not self.stub:
            logger.info(f"Connecting to gRPC server at {settings.GRPC_SERVER}")
            self.channel = grpc.aio.insecure_channel(settings.GRPC_SERVER)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            try:
                await self.channel.channel_ready()
                logger.info("gRPC connection established.")
            except grpc.aio.AioRpcError as e:
                logger.error(f"Failed to connect to gRPC server: {e.details()}")
                self.stub = None
                self.channel = None
                raise

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None
            logger.info("gRPC connection closed.")

    async def chat(self, query: str):
        if not self.stub:
            logger.error("gRPC client is not connected.")
            yield "[Error: AI service is not connected]"
            return
        request = inference_pb2.ChatRequest(query=query)
        try:
            async for resp in self.stub.ChatStream(request):
                if resp.HasField("token"): yield resp.token
                elif resp.HasField("error_message"):
                    error_msg = f"[AI Service Error: {resp.error_message}]"
                    logger.error(error_msg)
                    yield error_msg
                    break
        except grpc.aio.AioRpcError as e:
            error_msg = f"[gRPC Communication Error: {e.details()}]"
            logger.error(error_msg)
            yield error_msg

    # 【新增】批量嵌入的客户端调用方法
    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.stub:
            raise ConnectionError("gRPC client not connected.")
        if not texts:
            return []
        
        request = inference_pb2.EmbeddingBatchRequest(texts=texts)
        try:
            response = await self.stub.GetEmbeddingsBatch(request)
            return [list(embedding.values) for embedding in response.embeddings]
        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC call GetEmbeddingsBatch failed: {e.details()}")
            # 返回与输入文本数量相同的空列表，避免下游出错
            return [[] for _ in texts]

    # ... (list_models, switch_model 等方法保持不变) ...
    async def list_models(self):
        if not self.stub: raise Exception("gRPC client is not connected.")
        request = inference_pb2.Empty()
        response = await self.stub.ListAvailableModels(request)
        return {"generation_models": list(response.generation_models), "embedding_models": list(response.embedding_models), "current_generation_model": response.current_generation_model, "current_embedding_model": response.current_embedding_model, "device": getattr(response, "device", "") }

    async def switch_model(self, model_name: str, model_type_enum):
        if not self.stub: raise Exception("gRPC client is not connected.")
        request = inference_pb2.SwitchModelRequest(model_name=model_name, model_type=model_type_enum)
        response = await self.stub.SwitchModel(request)
        return response.success, response.message

grpc_client_manager = GrpcClientManager()