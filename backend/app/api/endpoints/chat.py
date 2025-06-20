import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import grpc

# --- Local Imports ---
# Assuming the project structure allows this import path
from ...core.grpc_client import grpc_client_manager
from ...protos import inference_pb2

# Create a new router for chat-related endpoints
router = APIRouter()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    Handles the real-time chat functionality over a WebSocket connection.
    It acts as a proxy between the user's client and the gRPC inference service.
    """
    await websocket.accept()
    logging.info(f"WebSocket connection accepted from {websocket.client.host}")

    # Get the gRPC stub to communicate with the inference service
    try:
        stub = grpc_client_manager.get_stub()
    except ConnectionError as e:
        logging.error(f"gRPC connection error: {e}")
        await websocket.close(code=1011, reason="Backend server cannot connect to AI service.")
        return

    try:
        while True:
            # 1. Wait for a message from the user's client
            user_query = await websocket.receive_text()
            logging.info(f"Received query from client: {user_query}")

            # 2. Create a gRPC request object
            grpc_request = inference_pb2.ChatRequest(query=user_query)

            # 3. Call the gRPC service and handle the stream
            try:
                # The 'ChatStream' method returns an async stream iterator
                async for grpc_response in stub.ChatStream(grpc_request):
                    if grpc_response.token:
                        # Stream the token back to the client
                        await websocket.send_text(grpc_response.token)
                    elif grpc_response.error_message:
                        # If an error occurs in the AI service, send it to the client
                        logging.error(f"Error from inference service: {grpc_response.error_message}")
                        await websocket.send_text(f"[ERROR]: {grpc_response.error_message}")
                        break # Stop processing this request on error

            except grpc.aio.AioRpcError as e:
                # Handle gRPC-specific errors (e.g., service unavailable)
                logging.error(f"A gRPC error occurred: {e.details()}")
                await websocket.send_text(f"[ERROR]: The AI service is currently unavailable. Details: {e.details()}")
                # We can choose to break the loop or allow the user to try again
                # For now, we continue the loop
                continue


    except WebSocketDisconnect:
        logging.info("WebSocket connection closed by client.")
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred in the chat WebSocket: {e}", exc_info=True)
        # Attempt to inform the client before closing
        await websocket.close(code=1011, reason=f"An internal server error occurred.")

