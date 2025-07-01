import logging
import os
from typing import List
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

# 核心修正：移除所有 'app.' 前缀
from core.config import EMBEDDING_MODEL_NAME
from core.db_client import vector_db

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, storage_dir: str | None = None):
        # The directory where uploaded knowledge documents are stored.
        # Default to '/knowledge_base_docs' so it matches the volume mount.
        self.storage_dir = storage_dir or os.getenv(
            "KNOWLEDGE_BASE_DOCS", "/knowledge_base_docs"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

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
        """Add a batch of already-created document chunks to the vector database."""
        if not documents:
            return
        logger.info(f"准备向知识库添加 {len(documents)} 个文档...")
        try:
            # SentenceTransformer.encode supports batch encoding and returns a list of vectors
            embeddings = self.encoder.encode([d.page_content for d in documents]).tolist()
            await vector_db.add_documents(documents, embeddings, document_source="batch")
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库。")
        except Exception as e:
            logger.error(f"添加文档到向量数据库时出错: {e}", exc_info=True)
            raise

    def list_documents(self) -> List[str]:
        """Return a list of filenames stored in the local knowledge directory."""
        return [
            f
            for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """Save an uploaded document to disk."""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return True

    async def embed_document(self, file_name: str):
        """Vectorize a stored document and push it to the vector database."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_name)

        with open(file_path, "rb") as f:
            content = f.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("gbk", errors="ignore")

        doc = Document(page_content=text)
        embedding = self.encoder.encode(text).tolist()
        await vector_db.add_documents([doc], [embedding], document_source=file_name)

    def delete_document(self, file_name: str) -> bool:
        """Remove a document from disk and the vector store."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        try:
            vector_db.delete_documents_by_source(file_name)
        except Exception:
            logger.warning("从向量数据库删除文档失败", exc_info=True)
        return True

    async def list_all_documents(self) -> List[dict]:
        """Return a list of stored document metadata."""
        return [{"source": name} for name in self.list_documents()]

    async def search(self, query: str, n_results: int = 3) -> List[Document]:
        """Search the vector database for documents relevant to ``query``."""
        logger.info(f"在知识库中搜索查询: '{query}' (请求 {n_results} 个结果)")
        try:
            query_vector = self.encoder.encode(query).tolist()
            results = await vector_db.search_with_vector(query_vector, top_k=n_results)
            logger.info(f"为查询 '{query}' 找到了 {len(results)} 个相关文档。")
            return results
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}", exc_info=True)
            return []


kb_service = KnowledgeBaseService()

