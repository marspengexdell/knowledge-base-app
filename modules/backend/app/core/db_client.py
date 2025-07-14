import os
import logging
import chromadb
from langchain_core.documents import Document
from typing import List

from services.embedding import embedding_model

logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    用于与 Chroma 本地嵌入式向量数据库交互的客户端。
    """

    def __init__(self):
        try:
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/app/chroma_store")

            self.client = chromadb.Client(
                settings=chromadb.Settings(
                    is_persistent=True,
                    persist_directory=persist_dir,
                )
            )

            self.collection_name = "knowledge_base_main_collection"
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            logger.info(f"成功初始化嵌入式 ChromaDB 集合: '{self.collection_name}'，目录: {persist_dir}")
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}", exc_info=True)
            raise

    async def add_documents(self, documents: List[Document], embeddings: List[List[float]], document_source: str):
        try:
            ids = [f"{document_source}_{i}" for i in range(len(documents))]
            metadatas = [{"source": document_source, "text": doc.page_content} for doc in documents]
            self.collection.add(embeddings=embeddings, metadatas=metadatas, ids=ids)
            logger.info(f"成功添加 {len(documents)} 个文档片段到集合中，来源: {document_source}")
        except Exception as e:
            logger.error(f"添加文档失败: {e}", exc_info=True)

    async def search_with_vector(self, query_embedding: List[float], top_k: int) -> List[Document]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"],
            )

            found_docs = []
            metas_list = results.get("metadatas", [[]])
            docs_list = results.get("documents", [[]])
            distances_list = results.get("distances", [[]])

            if metas_list and metas_list[0]:
                for i, metadata in enumerate(metas_list[0]):
                    text = metadata.get("text")
                    if not text and docs_list[0]:
                        text = docs_list[0][i]
                    distance = distances_list[0][i] if distances_list else None
                    metadata["distance"] = distance
                    if text:
                        found_docs.append(Document(page_content=text, metadata=metadata))

            logger.info(f"通过向量搜索找到 {len(found_docs)} 个文档。")
            return found_docs
        except Exception as e:
            logger.error(f"向量搜索失败: {e}", exc_info=True)
            return []

    async def asimilarity_search(self, query: str, k: int = 3) -> List[Document]:
        try:
            query_embedding = await embedding_model.embed(query)
            if not query_embedding:
                logger.warning("未能获得有效的 embedding。")
                return []
            return await self.search_with_vector(query_embedding, k)
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}", exc_info=True)
            return []

    def delete_documents_by_source(self, source: str):
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"已删除来源为 '{source}' 的文档。")
        except Exception as e:
            logger.error(f"删除文档失败: {e}", exc_info=True)


vector_db = VectorDBClient()
