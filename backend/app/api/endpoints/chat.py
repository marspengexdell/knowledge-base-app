from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.grpc_client import grpc_client_manager
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    Handles the WebSocket connection for chat.
    Accepts a connection, receives a user query, streams the AI response back token by token.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from: {websocket.client}")

    # Ensure gRPC client is connected before starting the chat loop
    if not grpc_client_manager.stub:
        logger.warning("gRPC client not connected, attempting to connect now.")
        try:
            await grpc_client_manager.connect()
        except Exception as e:
            logger.error(f"Failed to connect to gRPC service: {e}")
            await websocket.send_text("[System Error: Could not connect to AI service.]")
            await websocket.close()
            return

    try:
        while True:
            # Wait for a message from the client
            message = await websocket.receive_text()
            
            # The original code handled JSON or plain text. We can simplify to just expect text.
            # If the frontend sends JSON, it's better to standardize it.
            # Let's assume the frontend sends a plain text query for simplicity.
            user_query = message.strip()

            if not user_query:
                continue

            logger.info(f"Received query: {user_query}")
            
            try:
                # Asynchronously iterate through the tokens from the gRPC stream
                async for token in grpc_client_manager.chat(user_query):
                    # Send each token as a separate text message
                    await websocket.send_text(token)
            except Exception as e:
                logger.error(f"An error occurred during chat stream: {e}", exc_info=True)
                await websocket.send_text(f"[System Error: {e}]")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket handler: {e}", exc_info=True)