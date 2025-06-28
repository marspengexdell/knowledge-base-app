# backend/app/api/endpoints/chat.py (最终修正版)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.grpc_client import grpc_client_manager
from ...services.knowledge_base import kb_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def build_prompt_with_context(query: str, context: list[str]) -> str:
    """将用户问题和检索到的上下文拼接成一个增强的Prompt"""
    if not context:
        return query

    context_str = "\n\n".join(context)
    prompt = f"""
    请根据以下提供的上下文信息来回答用户的问题。请确保你的回答完全基于这些信息，不要使用任何外部知识。如果上下文信息不足以回答问题，请直接说“根据我掌握的知识，我无法回答这个问题”。

    上下文信息:
    ---
    {context_str}
    ---

    用户的问题是: {query}
    """
    return prompt.strip()


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from: {websocket.client}")

    try:
        while True:
            user_query = await websocket.receive_text()
            user_query = user_query.strip()
            if not user_query:
                continue

            try:
                # --- RAG 流程 ---
                logger.info(f"正在为查询 '{user_query}' 检索知识库...")
                
                # 【关键修复】在这里加上 await
                context = await kb_service.search(user_query, n_results=3)
                
                if context:
                    logger.info(f"知识库检索命中：{len(context)} 条片段")
                else:
                    logger.warning("未能从知识库中检索到任何相关上下文。")

                final_prompt = build_prompt_with_context(user_query, context)
                
                logger.info("正在将最终的Prompt发送到gRPC服务进行生成...")
                async for token in grpc_client_manager.chat(final_prompt):
                    await websocket.send_text(token)

            except Exception as e:
                error_msg = f"An error occurred during chat stream: {e}"
                logger.error(error_msg, exc_info=True)
                await websocket.send_text(f"[SYSTEM-ERROR] {error_msg}")
            finally:
                await websocket.send_text("[DONE]")
                logger.info("Chat stream finished.")

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket 处理程序中发生意外错误: {e}", exc_info=True)