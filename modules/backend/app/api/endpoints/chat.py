from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from core.grpc_client import grpc_client_manager
from services.knowledge_service import knowledge_service
from services.session_service import session_service
from protos import inference_pb2
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


def build_final_messages_for_grpc(
    query: str, context_docs: list[str], history: list[dict]
) -> list[dict]:
    final_messages = []
    if context_docs:
        context_str = "\n\n".join(context_docs)
        prompt = f"""
        请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
        请不要提及＜“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
        如果上下文信息不足以回答问题，请直接回答“根据我掌握的知识，我无法回答这个问题”。

        【上下文信息】
        ---
        {context_str}
        ---
        """
        final_messages.append({"role": "system", "content": prompt.strip()})

    final_messages.extend(history)
    final_messages.append({"role": "user", "content": query})
    return final_messages


@router.post("/")
async def chat_api(
    query: str = Body(..., embed=True), session_id: str | None = Body(default=None)
):
    if not session_id:
        session_id = session_service.create_session()

    history = session_service.get_session_context(session_id)

    try:
        context_docs = await kb_service.search(query, n_results=3)
        context_contents = [doc.page_content for doc in context_docs]
        messages_for_grpc = build_final_messages_for_grpc(
            query, context_contents, history
        )

        grpc_req = inference_pb2.ChatRequest(
            messages=[
                inference_pb2.Message(role=m["role"], content=m["content"])
                for m in messages_for_grpc
            ],
            session_id=session_id,
        )

        answer = ""
        async for token in grpc_client_manager.chat(grpc_req):
            answer += token

    except Exception as e:
        logger.error(f"HTTP chat API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    session_service.append_message(session_id, {"role": "user", "content": query})
    session_service.append_message(session_id, {"role": "assistant", "content": answer})

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

            if not session_id:
                session_id = data.get("session_id") or session_service.create_session()
                await websocket.send_text(
                    json.dumps({"event": "[ID]", "session_id": session_id})
                )

            if not user_query:
                continue

            history = session_service.get_session_context(session_id)
            context_docs = await knowledge_service.search(user_query, n_results=3)
            context_contents = [doc.page_content for doc in context_docs]
            messages_for_grpc = build_final_messages_for_grpc(
                user_query, context_contents, history
            )

            grpc_req = inference_pb2.ChatRequest(
                messages=[
                    inference_pb2.Message(role=m["role"], content=m["content"])
                    for m in messages_for_grpc
                ],
                session_id=session_id,
            )

            assistant_response = ""
            async for token in grpc_client_manager.chat(grpc_req):
                await websocket.send_text(
                    json.dumps({"token": token, "session_id": session_id})
                )
                assistant_response += token

            session_service.append_message(session_id, {"role": "user", "content": user_query})
            session_service.append_message(
                session_id, {"role": "assistant", "content": assistant_response}
            )

            await websocket.send_text(
                json.dumps({"event": "[DONE]", "session_id": session_id})
            )

    except WebSocketDisconnect:
        logger.info(f"\u5ba2\u6237\u7aef\u65ad\u5f00\u8fde\u63a5: {websocket.client}")
    except Exception as e:
        logger.error(
            f"WebSocket\u5904\u7406\u7a0b\u5e8f\u53d1\u751f\u610f\u5916\u9519\u8bef: {e}",
            exc_info=True,
        )
        if session_id and not websocket.client_state == "DISCONNECTED":
            await websocket.send_text(
                json.dumps(
                    {"event": "[ERROR]", "detail": str(e), "session_id": session_id}
                )
            )
