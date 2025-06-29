from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from ...core.grpc_client import grpc_client_manager
from ...services.knowledge_base import kb_service
from ...services.session_manager import (
    create_session,
    get_session_context,
    append_message,
)
from ...protos import inference_pb2
import logging
import json

END_TOKEN = "<END>"

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
async def chat_api(query: str = Body(..., embed=True), session_id: str | None = Body(default=None)):
    """HTTP endpoint for chat with optional session management."""
    if not session_id:
        session_id = create_session()

    # Retrieve history (unused in simple HTTP mode)
    _ = get_session_context(session_id)

    try:
        context = await kb_service.search(query, n_results=3)
        final_prompt = build_prompt_with_context(query, context)
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
    """Combine user question and retrieved context into one prompt."""
    if not context:
        return query

    context_str = "\n\n".join(context)
    prompt = f"""
    请根据以下提供的上下文信息来回答用户的问题。请确保你的回答完全基于这些信息，
不要使用任何外部知识。如果上下文信息不足以回答问题，请直接说“根据我掌握的知识，
我无法回答这个问题”。在回答时，请先分步骤思考，再给出最终的结论，
并在最终结论后输出 {END_TOKEN} 作为结束标记。

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
    session_id = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            user_query = data.get("query", "").strip()

            # Use existing session or create a new one
            session_id = data.get("session_id") or create_session()

            if not user_query:
                continue

            history = get_session_context(session_id)
            append_message(session_id, {"role": "user", "content": user_query})

            context = await kb_service.search(user_query, n_results=3)
            final_prompt_for_model = build_prompt_with_context(user_query, context)

            messages_for_grpc = history + [{"role": "user", "content": final_prompt_for_model}]
            grpc_req = inference_pb2.ChatRequest(
                messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages_for_grpc],
                session_id=session_id,
            )

            assistant_response = ""
            async for token in grpc_client_manager.chat(grpc_req):
                await websocket.send_text(json.dumps({"token": token, "session_id": session_id}))
                assistant_response += token

            append_message(session_id, {"role": "assistant", "content": assistant_response})
            await websocket.send_text(json.dumps({"event": "[DONE]", "session_id": session_id}))

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"Unexpected error in websocket handler: {e}", exc_info=True)

