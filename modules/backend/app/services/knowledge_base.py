import logging
from typing import List
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

# 核心修正：移除所有 'app.' 前缀
from core.config import EMBEDDING_MODEL_NAME
from core.db_client import vector_db

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.encoder = None
        self._load_encoder()

    def _load_encoder(self):
        try:
            self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info(f"成功加载嵌入模型: {EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}", exc_info=True)
            raise

    async def add_documents(self, documents: List[Document]):
        if not documents:
            return
        logger.info(f"准备向知识库添加 {len(documents)} 个文档...")
        try:
            await vector_db.add_documents(documents)
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库。")
        except Exception as e:
            logger.error(f"添加文档到向量数据库时出错: {e}", exc_info=True)
            raise

    async def search(self, query: str, n_results: int = 3) -> List[Document]:
        logger.info(f"在知识库中搜索查询: '{query}' (请求 {n_results} 个结果)")
        try:
            results = await vector_db.asimilarity_search(query, k=n_results)
            logger.info(f"为查询 '{query}' 找到了 {len(results)} 个相关文档。")
            return results
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}", exc_info=True)
            return []


kb_service = KnowledgeBaseService()

