import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body

# 核心修正：将所有 '...' 的相对导入改为 '..'
from ..core.grpc_client import grpc_client_manager
from ..services.knowledge_base import kb_service
from ..services.session_manager import (
    create_session,
    get_session_context,
    append_message,
)
from ..protos import inference_pb2

logger = logging.getLogger(__name__)
router = APIRouter()
END_TOKEN = "<END>" # 保持与旧代码一致，尽管在新逻辑中可能不直接使用

def build_prompt_with_context(query: str, context: list[str]) -> str:
    """
    将用户问题和检索到的上下文组合成一个专业的、用于RAG的Prompt。
    """
    # 注意：这个函数只在找到上下文时被调用。
    context_str = "\n\n---\n\n".join(context)
    prompt = f"""
    请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
    请不要提及“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
    如果上下文信息不足以回答问题，请直接回答“根据我掌握的知识，我无法回答这个问题”。

    【上下文信息】
    {context_str}

    【用户的问题】
    {query}
    """
    return prompt.strip()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    处理WebSocket聊天请求，包含“知识库优先，AI后备”的智能判断逻辑。
    """
    await websocket.accept()
    session_id = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            user_query = data.get("query", "").strip()
            
            if not user_query:
                continue

            # 使用或创建会话
            session_id = data.get("session_id") or create_session()
            history = get_session_context(session_id)
            append_message(session_id, {"role": "user", "content": user_query})

            # 步骤1: 首先在知识库中搜索相关文档
            logger.info(f"Session [{session_id}]: 正在为问题 '{user_query}' 搜索知识库...")
            context_docs = await kb_service.search(user_query, n_results=3)

            final_prompt_for_model = ""
            
            # 步骤2: 进行智能判断
            if context_docs:
                # --- 情况A: 在知识库中找到了相关内容 ---
                logger.info(f"Session [{session_id}]: 在知识库中找到相关内容，将使用知识库进行回答。")
                context_contents = [doc.page_content for doc in context_docs]
                final_prompt_for_model = build_prompt_with_context(user_query, context_contents)
            else:
                # --- 情况B: 未找到内容，切换到通用AI模式 ---
                logger.info(f"Session [{session_id}]: 知识库中未找到相关内容，将切换到通用AI模式。")
                
                # 发送一个“切换模式”的提示信息给前端
                fallback_message = "您好，您的问题超出了我的知识库范围。以下是由我的AI大脑为您提供的通用回答：\n\n"
                await websocket.send_text(json.dumps({"token": fallback_message, "session_id": session_id}))
                
                # 在通用模式下，直接使用用户的原始问题
                final_prompt_for_model = user_query

            # 步骤3: 构建gRPC请求并发送给大模型
            messages_for_grpc = history + [{"role": "user", "content": final_prompt_for_model}]
            grpc_req = inference_pb2.ChatRequest(
                messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
                session_id=session_id,
            )

            assistant_response = ""
            async for token in grpc_client_manager.chat(grpc_req):
                await websocket.send_text(json.dumps({"token": token, "session_id": session_id}))
                assistant_response += token
            
            # 步骤4: 保存完整的助手回复并结束
            append_message(session_id, {"role": "assistant", "content": assistant_response})
            await websocket.send_text(json.dumps({"event": "[DONE]", "session_id": session_id}))

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket处理程序发生意外错误: {e}", exc_info=True)
        # 可以在这里向客户端发送一个错误消息
        if session_id and websocket.client_state != WebSocketDisconnect:
             await websocket.send_text(json.dumps({"error": str(e), "session_id": session_id}))
