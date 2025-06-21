from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.config import settings

router = APIRouter()

@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    # 获取前端发来的 Origin
    origin = websocket.headers.get("origin")
    cors_list = settings.BACKEND_CORS_ORIGINS

    # 兼容字符串或列表格式
    if isinstance(cors_list, str):
        import json
        try:
            cors_list = json.loads(cors_list)
        except Exception:
            cors_list = [cors_list]

    # 调试打印（上线后可注释）
    print(f"DEBUG - WebSocket request origin: {origin}")
    print(f"DEBUG - WebSocket CORS whitelist: {cors_list}")

    # 严格校验Origin
    if origin in cors_list:
        await websocket.accept()
    else:
        await websocket.close(code=403)
        print(f"Connection rejected for origin: {origin}, allowed: {cors_list}")
        return

    # 后续业务逻辑
    try:
        while True:
            data = await websocket.receive_json()
            # 这里写你的处理逻辑...
            await websocket.send_json({"reply": f"Echo: {data}"})
    except WebSocketDisconnect:
        print("WebSocket disconnected")
