from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ....core.config import settings
from ....core.grpc_client import grpc_client_manager
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    cors_list = settings.BACKEND_CORS_ORIGINS
    if isinstance(cors_list, str):
        try:
            cors_list = json.loads(cors_list)
        except Exception:
            cors_list = [cors_list]
    if origin in cors_list:
        await websocket.accept()
    else:
        await websocket.close(code=403)
        print(f"Connection rejected for origin: {origin}, allowed: {cors_list}")
        return

    # 确保 gRPC 连接已建立
    if not grpc_client_manager.stub:
        await grpc_client_manager.connect()

    try:
        while True:
            text = await websocket.receive_text()
            if not text.strip():
                continue
            try:
                data = json.loads(text)
                user_query = data.get("query") or data.get("msg") or ""
            except Exception:
                user_query = text.strip()

            if not user_query:
                await websocket.send_json({"error": "No query/msg in message"})
                continue

            try:
                ai_reply = await grpc_client_manager.chat(user_query)
            except Exception as e:
                ai_reply = f"[AI服务异常]: {e}"

            await websocket.send_json({"reply": ai_reply})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
