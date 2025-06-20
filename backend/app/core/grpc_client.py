import grpc
import logging
import os
import sys

# --- Add protos to Python path ---
# Adjusting the path to correctly locate the 'protos' directory from 'core'
proto_path = os.path.join(os.path.dirname(__file__), '..', 'protos')
sys.path.append(proto_path)

# Now we can import the generated files
import inference_pb2
import inference_pb2_grpc


class GrpcClientManager:
    """
    A manager class to handle the gRPC channel and stub for the InferenceService.
    This ensures that the connection is created once and reused across the application.
    """
    def __init__(self):
        self.channel: grpc.aio.Channel | None = None
        self.stub: inference_pb2_grpc.InferenceServiceStub | None = None
        self.server_url = os.getenv("INFERENCE_SERVER_URL", os.getenv("GRPC_SERVER", "localhost:50051"))
        logging.info(f"gRPC client configured to connect to: {self.server_url}")

    async def connect(self):
        """
        Establishes the asynchronous gRPC channel and creates the stub.
        This method should be called during the application startup event.
        """
        if not self.channel:
            logging.info(f"Connecting to gRPC server at {self.server_url}...")
            # Create an asynchronous channel
            self.channel = grpc.aio.insecure_channel(self.server_url)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            logging.info("gRPC channel and stub created.")

    async def disconnect(self):
        """
        Closes the gRPC channel gracefully.
        This method should be called during the application shutdown event.
        """
        if self.channel:
            logging.info("Closing gRPC channel.")
            await self.channel.close()
            self.channel = None
            self.stub = None
            logging.info("gRPC channel closed.")

    def get_stub(self) -> inference_pb2_grpc.InferenceServiceStub:
        """
        Provides access to the gRPC stub.
        Raises an exception if the client is not connected.
        """
        if not self.stub:
            # This should ideally not happen if connect() is called at startup
            raise ConnectionError("gRPC client is not connected. Call connect() first.")
        return self.stub

# Create a single instance of the manager to be used throughout the application
grpc_client_manager = GrpcClientManager()
