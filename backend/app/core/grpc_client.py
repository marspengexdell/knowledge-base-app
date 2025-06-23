import grpc
from ..protos import inference_pb2, inference_pb2_grpc
from ..core.settings import settings
import logging

logger = logging.getLogger(__name__)

class GrpcClientManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        """
        Establishes an asynchronous connection to the gRPC server.
        """
        if not self.stub:
            logger.info(f"Connecting to gRPC server at {settings.GRPC_SERVER}")
            self.channel = grpc.aio.insecure_channel(settings.GRPC_SERVER)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            try:
                # Verify connection is ready
                await self.channel.channel_ready()
                logger.info("gRPC connection established.")
            except grpc.aio.AioRpcError as e:
                logger.error(f"Failed to connect to gRPC server: {e.details()}")
                self.stub = None
                self.channel = None
                raise

    async def disconnect(self):
        """
        Closes the gRPC connection.
        """
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None
            logger.info("gRPC connection closed.")

    async def chat(self, query: str):
        """
        Sends a query to the gRPC service and streams the response.
        This is an asynchronous generator.
        """
        if not self.stub:
            logger.error("gRPC client is not connected.")
            yield "[Error: AI service is not connected]"
            return

        request = inference_pb2.ChatRequest(query=query)
        try:
            # Asynchronously iterate over the streaming response from the gRPC server
            async for resp in self.stub.ChatStream(request):
                if resp.HasField("token"):
                    yield resp.token
                elif resp.HasField("error_message"):
                    error_msg = f"[AI Service Error: {resp.error_message}]"
                    logger.error(error_msg)
                    yield error_msg
                    break # Stop streaming on error
                # Source documents can be handled here if needed, e.g., yielded separately
                # For a pure chat stream, we might ignore them or collect and send at the end.
                # For now, we only yield the token to keep the stream clean.

        except grpc.aio.AioRpcError as e:
            error_msg = f"[gRPC Communication Error: {e.details()}]"
            logger.error(error_msg)
            yield error_msg

    async def list_models(self):
        if not self.stub:
            raise Exception("gRPC client is not connected.")
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
            raise Exception("gRPC client is not connected.")
        
        mtype = inference_pb2.ModelType.GENERATION
        if model_type.lower() == "embedding":
            mtype = inference_pb2.ModelType.EMBEDDING

        request = inference_pb2.SwitchModelRequest(model_name=model_name, model_type=mtype)
        response = await self.stub.SwitchModel(request)
        return response.success, response.message

# Singleton instance of the gRPC client manager
grpc_client_manager = GrpcClientManager()