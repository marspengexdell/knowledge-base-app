import logging
from fastapi.websockets import WebSocket
from langchain_core.documents import Document

from core.grpc_client import grpc_client_manager
from protos import inference_pb2
from services.knowledge_base import kb_service

logger = logging.getLogger(__name__)


class ChatService:
    async def handle_chat(self, websocket: WebSocket, session_id: str, query: str):
        """
        处理聊天请求的核心逻辑，包含“知识库优先，AI后备”的智能判断。
        """
        await websocket.accept()
        await websocket.send_json(
            {"session_id": session_id, "event": "[ID]", "token": session_id}
        )

        # 步骤 1: 首先在知识库中搜索相关文档
        logger.info(f"正在为问题: '{query}' 搜索知识库...")

        # 搜索最相关的3个文档片段
        context_docs = await kb_service.search(query=query, n_results=3)

        # 根据搜索结果构建提示信息和待发送的消息列表
        messages = []

        context_docs = kb_service.search(
            query=query, top_k=3



        if context_docs:
            # --- 情况 A: 在知识库中找到了相关内容 ---
            logger.info("在知识库中找到相关内容，将使用知识库进行回答。")


            context_text = "\n\n---\n\n".join(doc.page_content for doc in context_docs)
            prompt = (
                "请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。\n"
                "请不要提及“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。\n"
                "如果上下文信息不足以回答问题，请直接回答“我所掌握的知识无法回答您的问题”。\n\n"
                "【上下文信息】\n"
                f"{context_text}"
            )
            messages.append({"role": "system", "content": prompt})

            # 构建上下文文本
            context_text = "\n\n---\n\n".join(
                [doc.page_content for doc in context_docs]
            )

            # 构建“专业模式”的指令 (Prompt)
            prompt = f"""
            请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
            请不要提及“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
            如果上下文信息不足以回答问题，请直接回答“我所掌握的知识无法回答您的问题”。

            【上下文信息】
            {context_text}

            【用户的问题】
            {query}
            """

            # 将生成的回答流式传输回前端
            async for chunk in llm.astream(prompt):
                await websocket.send_json({"event": "[DATA]", "token": chunk})


        else:
            # --- 情况 B: 在知识库中未找到相关内容 (Fallback 逻辑) ---
            logger.info("知识库中未找到相关内容，将切换到通用AI模式进行回答。")

            fallback_message = (
                "您好，您的问题超出了我的知识库范围。以下是由我的AI大脑为您提供的通用回答：\n\n"
            )
            await websocket.send_json({"event": "[DATA]", "token": fallback_message})

        # 将用户问题加入对话消息
        messages.append({"role": "user", "content": query})

        # 构建 gRPC 请求并流式返回结果
        grpc_req = inference_pb2.ChatRequest(
            messages=[
                inference_pb2.Message(role=m["role"], content=m["content"])
                for m in messages
            ],
            session_id=session_id,
        )

        async for chunk in grpc_client_manager.chat(grpc_req):
            await websocket.send_json({"event": "[DATA]", "token": chunk})

        # 标记对话结束
        await websocket.send_json({"event": "[DONE]"})
        logger.info("回答完毕，关闭连接。")


chat_service = ChatService()
