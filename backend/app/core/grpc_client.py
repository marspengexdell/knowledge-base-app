import grpc
from ..protos import inference_pb2, inference_pb2_grpc
from ..core.config import settings

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        # 用 aio 异步连接
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
            # 按proto的定义判断返回的内容类型
            if resp.HasField("token"):
                reply += resp.token
            elif resp.HasField("error_message"):
                raise Exception(resp.error_message)
            elif resp.HasField("source_document"):
                reply += "\n[Source]: " + resp.source_document
        return reply

grpc_client_manager = GrpcClientManager()
