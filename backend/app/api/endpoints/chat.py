import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import grpc
from ...protos import inference_pb2, inference_pb2_grpc

router = APIRouter()
INFER_ADDR = "inference:50051"  # docker-compose服务名

@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logging.info(f"WebSocket connection accepted from {websocket.client.host}")

    # 创建 gRPC 连接（同步流）
    channel = grpc.insecure_channel(INFER_ADDR)
    stub = inference_pb2_grpc.InferenceServiceStub(channel)

    try:
        while True:
            # 前端应该发json，带 query
            data = await websocket.receive_json()
            user_query = data.get("query")
            session_id = data.get("session_id", "")
            if not user_query:
                await websocket.send_json({"error": "query is required"})
                continue

            grpc_request = inference_pb2.ChatRequest(query=user_query, session_id=session_id)
            try:
                # 同步流式gRPC调用，阻塞主线程，所以用run_in_executor
                def stream_tokens():
                    for grpc_response in stub.ChatStream(grpc_request):
                        if grpc_response.token:
                            yield {"token": grpc_response.token}
                        elif grpc_response.error_message:
                            yield {"error": grpc_response.error_message}
                            break

                import asyncio
                loop = asyncio.get_event_loop()
                async for resp in _to_async_iter(loop, stream_tokens()):
                    await websocket.send_json(resp)

            except grpc.RpcError as e:
                logging.error(f"gRPC error: {e}")
                await websocket.send_json({"error": f"AI服务异常: {e.details()}"})
                continue

    except WebSocketDisconnect:
        logging.info("WebSocket connection closed by client.")
    except Exception as e:
        logging.error(f"Unexpected WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error.")

# 将同步生成器转 async 生成器
async def _to_async_iter(loop, sync_gen):
    for item in sync_gen:
        yield item
