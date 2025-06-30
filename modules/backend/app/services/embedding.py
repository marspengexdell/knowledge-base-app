from core.grpc_client import grpc_client_manager
from typing import List
import asyncio # 【新增】导入asyncio

class EmbeddingModel:
    """
    一个封装了 gRPC 客户端的嵌入服务。
    它不直接加载模型，而是通过 gRPC 请求 inference 服务来获取嵌入。
    """
    def __init__(self):
        self.grpc_client = grpc_client_manager

    # 【修改】将批量方法修改为异步，以匹配gRPC客户端
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # 调用 gRPC 客户端的异步方法
        return await self.grpc_client.get_embeddings_batch(texts)
    
    # 【可选保留】单个嵌入的方法，以防未来需要
    async def embed(self, text: str) -> List[float]:
        if not text.strip():
            return []
        results = await self.embed_batch([text])
        return results[0] if results else []

embedding_model = EmbeddingModel()
