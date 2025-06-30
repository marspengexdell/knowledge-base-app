import logging
from fastapi.websockets import WebSocket
from langchain_core.documents import Document

from ...core.llm_client import llm
from .knowledge_base import kb_service

logger = logging.getLogger(__name__)

class ChatService:
    async def handle_chat(self, websocket: WebSocket, session_id: str, query: str):
        """
        处理聊天请求的核心逻辑，包含“知识库优先，AI后备”的智能判断。
        """
        await websocket.accept()
        await websocket.send_json({"session_id": session_id, "event": "[ID]", "token": session_id})

        # 步骤 1: 首先在知识库中搜索相关文档
        logger.info(f"正在为问题: '{query}' 搜索知识库...")
        context_docs = kb_service.search(query=query, top_k=3) # 搜索最相关的3个文档片段

        # 步骤 2: 进行智能判断
        if context_docs:
            # --- 情况 A: 在知识库中找到了相关内容 ---
            logger.info("在知识库中找到相关内容，将使用知识库进行回答。")

            # 构建上下文文本
            context_text = "\n\n---\n\n".join([doc.page_content for doc in context_docs])

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

            # 首先，发送一个“切换模式”的提示信息
            # 这个提示信息会立即显示在前端，告知用户当前的情况
            # 支持多语言的关键：可以根据用户query的语言来选择不同的提示语
            fallback_message = "您好，您的问题超出了我的知识库范围。以下是由我的AI大脑为您提供的通用回答：\n\n"
            await websocket.send_json({"event": "[DATA]", "token": fallback_message})

            # 然后，让大模型直接用自己的知识来回答用户的问题
            # 我们直接将用户的原始问题作为 Prompt
            async for chunk in llm.astream(query):
                await websocket.send_json({"event": "[DATA]", "token": chunk})

        # 标记对话结束
        await websocket.send_json({"event": "[DONE]"})
        logger.info("回答完毕，关闭连接。")


chat_service = ChatService()
