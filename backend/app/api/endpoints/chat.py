import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import grpc
from ...protos import inference_pb2, inference_pb2_grpc
import asyncio

router = APIRouter()
INFER_ADDR = "inference:50051"

@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logging.info(f"WebSocket connection accepted from {websocket.client.host}")

    channel = grpc.insecure_channel(INFER_ADDR)
    stub = inference_pb2_grpc.InferenceServiceStub(channel)

    try:
        while True:
            data = await websocket.receive_json()
            user_query = data.get("query")
            session_id = data.get("session_id", "")
            if not user_query:
                await websocket.send_json({"error": "query is required"})
                continue

            grpc_request = inference_pb2.ChatRequest(query=user_query, session_id=session_id)
            try:
                # 用线程池防止阻塞 event loop
                loop = asyncio.get_running_loop()
                def sync_stream():
                    for grpc_response in stub.ChatStream(grpc_request):
                        if grpc_response.token:
                            yield {"token": grpc_response.token}
                        elif grpc_response.error_message:
                            yield {"error": grpc_response.error_message}
                            break
                # 用 run_in_executor 包装同步生成器为 async
                async for resp in to_async_stream(loop, sync_stream):
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

# 核心改动：同步生成器转异步流
async def to_async_stream(loop, sync_gen_fn):
    def run():
        # 返回一个迭代器
        return sync_gen_fn()
    # 用 run_in_executor 包装整个生成器的遍历
    it = await loop.run_in_executor(None, run)
    try:
        while True:
            # 下一个token也用run_in_executor
            item = await loop.run_in_executor(None, next, it, None)
            if item is None:
                break
            yield item
    except StopIteration:
        pass
