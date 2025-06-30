import logging
from typing import List
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

# 核心修正：将所有 '..' 相对导入改为 'app.' 绝对导入
from app.core.config import EMBEDDING_MODEL_NAME
from app.core.db_client import vector_db
# (注意：如果未来添加其他来自 core 或 services 的导入，也应遵循此模式)

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        """
        知识库服务，封装了文档的向量化、存储和搜索功能。
        """
        self.encoder = None
        self._load_encoder()

    def _load_encoder(self):
        """加载或初始化嵌入模型。"""
        try:
            # 这里的模型名称从配置文件中读取
            self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info(f"成功加载嵌入模型: {EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}", exc_info=True)
            # 在无法加载模型时，可以选择抛出异常或进行其他处理
            raise

    async def add_documents(self, documents: List[Document]):
        """
        将文档内容和元数据添加到向量数据库中。
        """
        if not documents:
            return
        
        logger.info(f"准备向知识库添加 {len(documents)} 个文档...")
        try:
            # LangChain 的 Chroma 集成通常会自动处理文本的编码/向量化
            await vector_db.add_documents(documents)
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库。")
        except Exception as e:
            logger.error(f"添加文档到向量数据库时出错: {e}", exc_info=True)
            raise

    async def search(self, query: str, n_results: int = 3) -> List[Document]:
        """
        根据用户查询，在向量数据库中进行相似度搜索。
        """
        logger.info(f"在知识库中搜索查询: '{query}' (请求 {n_results} 个结果)")
        try:
            # 使用相似度搜索功能
            results = await vector_db.asimilarity_search(query, k=n_results)
            logger.info(f"为查询 '{query}' 找到了 {len(results)} 个相关文档。")
            return results
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}", exc_info=True)
            # 返回空列表或重新抛出异常，取决于你的错误处理策略
            return []

# 创建一个服务实例，以便在应用中其他地方可以导入和使用
kb_service = KnowledgeBaseService()