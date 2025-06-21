from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.config import settings

router = APIRouter()

@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    # 获取 origin，做白名单校验
    origin = websocket.headers.get("origin")
    print(f"WebSocket connection from origin: {origin}")

    # 如果未配置白名单，直接accept（开发用）
    if not hasattr(settings, "BACKEND_CORS_ORIGINS") or not settings.BACKEND_CORS_ORIGINS:
        await websocket.accept()
    else:
        # pydantic会把JSON字符串自动转为list
        cors_list = settings.BACKEND_CORS_ORIGINS
        # 如果是字符串而不是list，尝试手动转一下
        if isinstance(cors_list, str):
            import json
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

    # 后续你的逻辑...
    try:
        while True:
            data = await websocket.receive_json()
            # ...
    except WebSocketDisconnect:
        print("WebSocket disconnected")
