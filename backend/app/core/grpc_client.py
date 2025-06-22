import grpc
from ..protos import inference_pb2, inference_pb2_grpc
from ..core.config import settings

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        # 用 aio 异步连接
        if not self.channel:
            self.channel = grpc.aio.insecure_channel(settings.GRPC_SERVER)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None

    async def chat(self, query):
        if not self.stub:
            raise Exception("gRPC未连接")
        request = inference_pb2.ChatRequest(query=query)
        reply = ""
        async for resp in self.stub.ChatStream(request):
            if resp.HasField("token"):
                reply += resp.token
            elif resp.HasField("error_message"):
                raise Exception(resp.error_message)
            elif resp.HasField("source_document"):
                reply += "\n[Source]: " + resp.source_document
        return reply

    async def list_models(self):
        if not self.stub:
            raise Exception("gRPC未连接")
        request = inference_pb2.Empty()
        response = await self.stub.ListAvailableModels(request)
        return {
            "generation_models": list(response.generation_models),
            "embedding_models": list(response.embedding_models),
            "current_generation_model": response.current_generation_model,
            "current_embedding_model": response.current_embedding_model
        }

    async def switch_model(self, model_name: str, model_type: str = "generation"):
        if not self.stub:
            raise Exception("gRPC未连接")
        # 对应 Proto 中的枚举值
        if model_type.lower() == "embedding":
            mtype = inference_pb2.ModelType.EMBEDDING
        else:
            mtype = inference_pb2.ModelType.GENERATION
        request = inference_pb2.SwitchModelRequest(model_name=model_name, model_type=mtype)
        response = await self.stub.SwitchModel(request)
        return response.success, response.message

grpc_client_manager = GrpcClientManager()
