from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.grpc_client import grpc_client_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from: {websocket.client}")

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
            user_query = await websocket.receive_text()
            user_query = user_query.strip()
            if not user_query:
                continue

            logger.info(f"Received query: {user_query}")

            try:
                async for token in grpc_client_manager.chat(user_query):
                    # ===== 彻底干掉所有token里的[DONE] =====
                    clean_token = token.replace("[DONE]", "").strip()
                    if not clean_token:
                        continue
                    await websocket.send_text(clean_token)
            except Exception as e:
                logger.error(f"An error occurred during chat stream: {e}", exc_info=True)
                await websocket.send_text(f"[System Error: {e}]")
            finally:
                await websocket.send_text("[DONE]")
                logger.info("Sent [DONE] signal to client.")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket handler: {e}", exc_info=True)
