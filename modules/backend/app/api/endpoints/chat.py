from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
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

END_TOKEN = "<END>"

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
async def chat_api(
    query: str = Body(..., embed=True),
    session_id: str | None = Body(default=None)
):
    """HTTP endpoint for chat with optional session management."""
    if not session_id:
        session_id = create_session()

    _ = get_session_context(session_id)

    try:
        context_docs = await kb_service.search(query, n_results=3)
        context_contents = [doc.page_content for doc in context_docs]
        final_prompt = build_prompt_with_context(query, context_contents)

        messages_for_grpc = [{"role": "user", "content": final_prompt}]
        grpc_req = inference_pb2.ChatRequest(
            messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
            session_id=session_id,
        )
        answer = ""
        async for token in grpc_client_manager.chat(grpc_req):
            answer += token
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    append_message(session_id, {"role": "user", "content": query})
    append_message(session_id, {"role": "assistant", "content": answer})

    return {"session_id": session_id, "answer": answer}


def build_prompt_with_context(query: str, context: list[str]) -> str:
    """将用户问题和检索到的上下文组合成一个专业的、用于RAG的Prompt。"""
    if not context:
        # 如果没有上下文，直接返回原始问题，或根据需要返回通用回答的指令
        return f"请用你的通用知识回答以下问题: {query}"

    context_str = "\n\n".join(context)
    prompt = f"""
    请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
    请不要提及“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
    如果上下文信息不足以回答问题，请直接回答“根据我掌握的知识，我无法回答这个问题”。

    【上下文信息】
    ---
    {context_str}
    ---

    【用户的问题是】: {query}
    """
    return prompt.strip()


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            user_query = data.get("query", "").strip()

            session_id = data.get("session_id") or create_session()

            if not user_query:
                continue

            history = get_session_context(session_id)
            append_message(session_id, {"role": "user", "content": user_query})

            context_docs = await kb_service.search(user_query, n_results=3)
            context_contents = [doc.page_content for doc in context_docs]
            final_prompt_for_model = build_prompt_with_context(user_query, context_contents)

            messages_for_grpc = history + [{"role": "user", "content": final_prompt_for_model}]
            grpc_req = inference_pb2.ChatRequest(
                messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
                session_id=session_id,
            )

            assistant_response = ""
            # 首先发送一个包含 session_id 的初始消息
            await websocket.send_text(json.dumps({"event": "[ID]", "session_id": session_id}))

            async for token in grpc_client_manager.chat(grpc_req):
                await websocket.send_text(json.dumps({"token": token, "session_id": session_id}))
                assistant_response += token

            append_message(session_id, {"role": "assistant", "content": assistant_response})
            await websocket.send_text(json.dumps({"event": "[DONE]", "session_id": session_id}))

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket处理程序发生意外错误: {e}", exc_info=True)
