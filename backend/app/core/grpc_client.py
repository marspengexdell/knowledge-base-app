import grpc
from ..protos import inference_pb2, inference_pb2_grpc
from ..core.config import settings

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        # 用aio异步连接
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
        # ChatStream 返回一个异步生成器
        reply = ""
        async for resp in self.stub.ChatStream(request):
            # ChatResponse对象，每次resp.text一部分内容（取决于你的proto实现）
            reply += resp.text  # 注意字段名，可能叫 message/answer/content/response，看你的proto
        return reply

grpc_client_manager = GrpcClientManager()
