import grpc
import app.protos.inference_pb2 as inference_pb2
import app.protos.inference_pb2_grpc as inference_pb2_grpc
from app.core.settings import settings
import logging
from typing import List

logger = logging.getLogger(__name__)

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        self.channel = grpc.aio.insecure_channel(settings.GRPC_SERVER)
        self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
        await self.channel.channel_ready()
        logger.info("Connected to gRPC server")

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
        self.stub = None
        self.channel = None
        logger.info("Disconnected from gRPC server")

    async def chat(self, query: str):
        if not self.stub:
            yield "[Error: no connection]"
            return
        req = inference_pb2.ChatRequest(query=query)
        async for resp in self.stub.ChatStream(req):
            if resp.HasField("token"):
                yield resp.token
            else:
                yield f"[Error: {resp.error_message}]"

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.stub:
            raise ConnectionError
        if not texts:
            return []
        req = inference_pb2.EmbeddingBatchRequest(texts=texts)
        resp = await self.stub.GetEmbeddingsBatch(req)
        return [list(e.values) for e in resp.embeddings]

    async def list_models(self):
        req = inference_pb2.Empty()
        resp = await self.stub.ListAvailableModels(req)
        return {
            "generation_models": list(resp.generation_models),
            "embedding_models": list(resp.embedding_models),
            "current_generation_model": resp.current_generation_model,
            "current_embedding_model": resp.current_embedding_model,
            "device": getattr(resp, "device", "")
        }

    async def switch_model(self, model_name: str, model_type_enum):
        req = inference_pb2.SwitchModelRequest(model_name=model_name, model_type=model_type_enum)
        resp = await self.stub.SwitchModel(req)
        return resp.success, resp.message

grpc_client_manager = GrpcClientManager()
