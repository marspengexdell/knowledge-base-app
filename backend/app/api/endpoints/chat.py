from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.grpc_client import grpc_client_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def print_debug(message):
    """一个带高亮标记的打印函数"""
    print(f"\n--- [BACKEND DEBUG] --- {message}\n", flush=True)

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from: {websocket.client}")

    if not grpc_client_manager.stub:
        try:
            await grpc_client_manager.connect()
        except Exception as e:
            await websocket.send_text("[System Error: Could not connect to AI service.]")
            await websocket.close()
            return

    try:
        while True:
            user_query = await websocket.receive_text()
            user_query = user_query.strip()
            if not user_query:
                continue

            # ★ 核心调试点 ★
            print_debug(f"STEP A: WebSocket 收到用户输入: '{user_query}'")

            try:
                # 调用gRPC服务并流式接收结果
                async for token in grpc_client_manager.chat(user_query):
                    # ★ 核心调试点 ★
                    print_debug(f"STEP B: 从 Inference 服务收到 token: '{token}'")
                    clean_token = token.replace("[DONE]", "").strip()
                    if not clean_token:
                        continue
                    await websocket.send_text(clean_token)
            except Exception as e:
                logger.error(f"An error occurred during chat stream: {e}", exc_info=True)
                await websocket.send_text(f"[System Error: {e}]")
            finally:
                await websocket.send_text("[DONE]")
                print_debug("STEP C: 对话结束，已发送 [DONE] 信号到前端。")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket handler: {e}", exc_info=True)
