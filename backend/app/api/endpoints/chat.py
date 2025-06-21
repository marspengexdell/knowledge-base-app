from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.config import settings
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    print("\n=== WEBSOCKET HANDLER ENTERED ===\n")
    origin = websocket.headers.get("origin")
    cors_list = settings.BACKEND_CORS_ORIGINS
    if isinstance(cors_list, str):
        try:
            cors_list = json.loads(cors_list)
        except Exception:
            cors_list = [cors_list]
    print(f"\n=== DEBUG ===\nWebSocket request origin: {origin}\nWebSocket CORS whitelist: {cors_list}\n=== END DEBUG ===\n")

    if origin in cors_list:
        await websocket.accept()
    else:
        await websocket.close(code=403)
        print(f"Connection rejected for origin: {origin}, allowed: {cors_list}")
        return

    try:
        while True:
            text = await websocket.receive_text()
            if not text.strip():
                continue  # 跳过空包
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                print(f"Invalid JSON received: {text}")
                continue

            await websocket.send_json({"reply": f"Echo: {data}"})
    except WebSocketDisconnect:
        print("WebSocket disconnected")

@router.get("/debug")
async def chat_debug():
    print("=== /chat/debug hit ===")
    return {"msg": "debug ok"}
