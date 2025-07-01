import logging
import os
from typing import List

from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

from core.config import EMBEDDING_MODEL_NAME
from core.db_client import vector_db
from services.embedding import embedding_model

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, storage_dir: str = "/knowledge_base_docs"):
        self.encoder = None
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_encoder()

    def _load_encoder(self):
        try:
            self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info(f"成功加载嵌入模型: {EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}", exc_info=True)
            raise

    def add_document(self, file_name: str, file_data: bytes) -> str:
        """Save an uploaded file to the knowledge base."""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"文档 '{file_name}' 已保存到 '{file_path}'")
        return file_path

    async def embed_document(self, file_name: str) -> bool:
        """Embed the specified document and store it in the vector DB."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        with open(file_path, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("gbk", errors="ignore")
        doc = Document(page_content=text, metadata={"source": file_name})
        embedding = await embedding_model.embed(text)
        await vector_db.add_documents([doc], [embedding], file_name)
        return True

    def list_documents(self) -> List[str]:
        """List file names stored in the knowledge base directory."""
        return [
            f
            for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    async def list_all_documents(self) -> List[dict] | None:
        """List all documents stored in the vector database."""
        try:
            results = vector_db.collection.get(include=["metadatas"], limit=None)
            sources = []
            seen = set()
            for meta in results.get("metadatas", []):
                src = meta.get("source")
                if src and src not in seen:
                    seen.add(src)
                    sources.append({"source": src})
            return sources
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}", exc_info=True)
            return None

    def delete_document(self, file_name: str) -> bool:
        """Delete a document from storage and vector database."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        vector_db.delete_documents_by_source(file_name)
        logger.info(f"文档 '{file_name}' 已被删除")
        return True

    async def delete_documents_by_source(self, source_name: str) -> bool:
        """Async wrapper to remove documents by source name."""
        result = self.delete_document(source_name)
        return result

    async def add_documents(self, documents: List[Document], document_source: str):
        if not documents:
            return
        logger.info(f"准备向知识库添加 {len(documents)} 个文档...")
        try:
            texts = [d.page_content for d in documents]
            embeddings = await embedding_model.embed_batch(texts)
            await vector_db.add_documents(documents, embeddings, document_source)
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

