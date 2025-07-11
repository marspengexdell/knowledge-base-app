import logging
from fastapi.websockets import WebSocket

from core.grpc_client import grpc_client_manager
from protos import inference_pb2
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

class ChatService:
    async def handle_chat(self, websocket: WebSocket, session_id: str, query: str):
        """
        RAG模式：有知识库就知识库作答，没有就用大模型“自由发挥”。
        """
        await websocket.accept()

        # 🔍 输入清洗
        query = query.strip()
        if not query:
            await websocket.send_json({
                "session_id": session_id,
                "event": "[ERROR]",
                "message": "请输入有效问题"
            })
            await websocket.close()
            return

        await websocket.send_json({
            "session_id": session_id,
            "event": "[ID]",
            "token": session_id
        })

        try:
            logger.info(f"正在为问题 '{query}' 检索知识库...")
            context_docs = await knowledge_service.search(query=query, n_results=3)
            context_docs = [doc for doc in context_docs if doc.page_content and doc.page_content.strip()]
            
            messages = []

            if context_docs:
                logger.info("知识库命中，将使用知识库内容回答。")
                context_text = "\n".join([f"片段{i+1}：{doc.page_content}" for i, doc in enumerate(context_docs)])
                prompt = (
                    "你是知识库问答助手，请严格依据下方提供的知识片段内容专业、直接地回答用户问题，不得编造和发挥。\n"
                    "如果下方片段都无法回答，回复“知识库未收录”。\n"
                    f"【知识片段】\n{context_text}\n"
                    f"【用户问题】：{query}\n"
                    "【你的回答】："
                )
                messages.append({"role": "system", "content": prompt})
            else:
                logger.info("知识库未命中，直接用AI大模型自由答。")
                messages.append({"role": "user", "content": query})

            # ✅ 可扩展参数：如 temperature, top_p（如模型支持）
            grpc_req = inference_pb2.ChatRequest(
                messages=[inference_pb2.Message(role=m["role"], content=m["content"]) for m in messages],
                session_id=session_id,
                temperature=0.7,
                top_p=0.9,
            )

            async for chunk in grpc_client_manager.chat(grpc_req):
                await websocket.send_json({"event": "[DATA]", "token": chunk})

            await websocket.send_json({"event": "[DONE]"})
            logger.info("回答完毕，关闭连接。")

        except Exception as e:
            logger.error(f"WebSocket 会话失败: {e}", exc_info=True)
            await websocket.send_json({
                "event": "[ERROR]",
                "message": "系统错误，请稍后再试"
            })

        finally:
            await websocket.close()

chat_service = ChatService()
