from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
# 核心修正：使用从 'app' 包开始的绝对导入路径
from app.core.grpc_client import grpc_client_manager
from app.services.knowledge_base import kb_service
from app.services.session_manager import (
    create_session,
    get_session_context,
    append_message,
)
from app.protos import inference_pb2
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

def build_final_messages_for_grpc(query: str, context_docs: list[str], history: list[dict]) -> list[dict]:
    """
    一个健壮的函数，用于构建发送到gRPC服务的最终消息列表。
    它将上下文、历史记录和当前问题智能地组合起来。
    """
    final_messages = []
    
    # 1. 将检索到的上下文作为 "system" 角色的消息
    # 这为AI提供了清晰的、最高优先级的指令和信息源
    if context_docs:
        context_str = "\n\n".join(context_docs)
        prompt = f"""
        请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
        请不要提及“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
        如果上下文信息不足以回答问题，请直接回答“根据我掌握的知识，我无法回答这个问题”。

        【上下文信息】
        ---
        {context_str}
        ---
        """
        final_messages.append({"role": "system", "content": prompt.strip()})
    
    # 2. 追加历史消息
    final_messages.extend(history)
    
    # 3. 追加当前用户的提问
    final_messages.append({"role": "user", "content": query})
    
    return final_messages

@router.post("/")
async def chat_api(query: str = Body(..., embed=True), session_id: str | None = Body(default=None)):
    """HTTP端点，支持多轮对话。"""
    if not session_id:
        session_id = create_session()

    history = get_session_context(session_id)
    
    try:
        # RAG流程：检索 -> 构建消息 -> 请求模型
        context_docs = await kb_service.search(query, n_results=3)
        context_contents = [doc.page_content for doc in context_docs]
        
        # 使用新的构建函数
        messages_for_grpc = build_final_messages_for_grpc(query, context_contents, history)
        
        grpc_req = inference_pb2.ChatRequest(
            messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
            session_id=session_id,
        )
        
        answer = ""
        async for token in grpc_client_manager.chat(grpc_req):
            answer += token
            
    except Exception as e:
        logger.error(f"HTTP chat API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    # 在返回前，将当前问答对保存到会话历史中
    append_message(session_id, {"role": "user", "content": query})
    append_message(session_id, {"role": "assistant", "content": answer})

    return {"session_id": session_id, "answer": answer}

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            user_query = data.get("query", "").strip()

            # 如果没有提供 session_id，则创建一个新的
            if not session_id:
                session_id = data.get("session_id") or create_session()
                # 立即将 session_id 发送给客户端，以便后续请求使用
                await websocket.send_text(json.dumps({"event": "[ID]", "session_id": session_id}))

            if not user_query:
                continue

            history = get_session_context(session_id)

            # RAG 流程
            context_docs = await kb_service.search(user_query, n_results=3)
            context_contents = [doc.page_content for doc in context_docs]
            
            # 使用统一的构建函数
            messages_for_grpc = build_final_messages_for_grpc(user_query, context_contents, history)

            grpc_req = inference_pb2.ChatRequest(
                messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
                session_id=session_id,
            )

            assistant_response = ""
            async for token in grpc_client_manager.chat(grpc_req):
                await websocket.send_text(json.dumps({"token": token, "session_id": session_id}))
                assistant_response += token
            
            # 保存当前的问与答
            append_message(session_id, {"role": "user", "content": user_query})
            append_message(session_id, {"role": "assistant", "content": assistant_response})
            
            # 发送结束标志
            await websocket.send_text(json.dumps({"event": "[DONE]", "session_id": session_id}))

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket处理程序发生意外错误: {e}", exc_info=True)
        if session_id and not websocket.client_state == 'DISCONNECTED':
            await websocket.send_text(json.dumps({"event": "[ERROR]", "detail": str(e), "session_id": session_id}))