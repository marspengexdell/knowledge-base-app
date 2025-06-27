from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.grpc_client import grpc_client_manager
from ...services.knowledge_base import kb_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def build_prompt_with_context(query: str, context: list[str]) -> str:
    """把检索到的内容和用户问题拼成最终的Prompt（RAG Prompt）"""
    if not context:
        return query
    context_str = "\n\n".join(context)
    prompt = f"""
你是一名智能知识助手。请仅根据下方知识库资料内容，准确回答用户问题。如资料不足请说“不知道”或“资料未覆盖”。

【知识库资料】
{context_str}

【用户提问】
{query}
"""
    return prompt.strip()

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
            try:
                # 1. 检索相关知识片段
                context = kb_service.search(user_query, n_results=2)
                logger.info(f"知识库检索命中：{len(context)} 条片段")
                # 2. 拼成prompt
                final_prompt = build_prompt_with_context(user_query, context)
                # 3. 送进大模型
                async for token in grpc_client_manager.chat(final_prompt):
                    await websocket.send_text(token)
            except Exception as e:
                logger.error(f"An error occurred during chat stream: {e}", exc_info=True)
                await websocket.send_text(f"[系统错误: {e}]")
            finally:
                await websocket.send_text("[DONE]")
                logger.info("Chat stream finished.")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket handler: {e}", exc_info=True)
