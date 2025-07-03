import os
import logging
import chromadb
from langchain_core.documents import Document
from typing import List
from urllib.parse import urlparse

from services.embedding import embedding_model

logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    专门用于与Chroma向量数据库交互的客户端。
    """

    def __init__(self):
        # 从环境变量获取ChromaDB的URL
        db_url_str = os.getenv("VECTOR_DB_URL", "http://vector-db:8000")
        logger.info(f"正在连接到向量数据库: {db_url_str}")

        try:
            parsed_url = urlparse(db_url_str)
            db_host = parsed_url.hostname
            db_port = parsed_url.port

            if not db_host or not db_port:
                raise ValueError("无效的 VECTOR_DB_URL，无法解析 host 或 port")

            self.client = chromadb.HttpClient(
                host=db_host,
                port=db_port,
                settings=chromadb.Settings(
                    is_persistent=True,
                ),
            )
            self.collection_name = "knowledge_base_main_collection"
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            logger.info(
                f"成功连接到向量数据库，并获取/创建集合: '{self.collection_name}'"
            )
        except Exception as e:
            logger.error(f"连接向量数据库失败: {e}", exc_info=True)
            raise

    async def add_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]],
        document_source: str,
    ):
        try:
            ids = [f"{document_source}_{i}" for i in range(len(documents))]
            metadatas = [
                {"source": document_source, "text": doc.page_content}
                for doc in documents
            ]
            self.collection.add(embeddings=embeddings, metadatas=metadatas, ids=ids)
            logger.info(
                f"成功向集合 '{self.collection_name}' 中添加了 {len(documents)} 个文档片段，来源: {document_source}。"
            )
        except Exception as e:
            logger.error(f"添加文档到向量数据库时出错: {e}", exc_info=True)

    async def search_with_vector(
        self, query_embedding: List[float], top_k: int
    ) -> List[Document]:
        """
        使用一个给定的查询向量，在数据库中执行相似度搜索。
        自动兼容 metadata["text"]/documents 任意一种返回结构。
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"],  # 强制返回所有
            )

            found_docs = []
            metas_list = results.get("metadatas", [[]])
            docs_list = results.get("documents", [[]])
            distances_list = results.get("distances", [[]])

            # 只遍历元数据（因为内容常在 metadata['text']）
            if metas_list and metas_list[0]:
                for i, metadata in enumerate(metas_list[0]):
                    text = metadata.get("text", None)
                    if not text and docs_list and docs_list[0] and len(docs_list[0]) > i:
                        text = docs_list[0][i]
                    distance = distances_list[0][i] if distances_list and len(distances_list[0]) > i else None
                    metadata = dict(metadata) if metadata else {}
                    metadata["distance"] = distance
                    if text is None or text == "":
                        logger.warning(f"第 {i} 个搜索结果内容为 None 或空，跳过。")
                        continue
                    found_docs.append(Document(page_content=text, metadata=metadata))

            logger.info(f"通过向量搜索找到了 {len(found_docs)} 个相关文档。")
            return found_docs
        except Exception as e:
            logger.error(f"在向量数据库中通过向量搜索时出错: {e}", exc_info=True)
            return []

    async def asimilarity_search(self, query: str, k: int = 3) -> List[Document]:
        try:
            query_embedding = await embedding_model.embed(query)
            if not query_embedding:
                logger.warning("未能获得查询的 embedding，直接返回空结果。")
                return []
            return await self.search_with_vector(query_embedding, k)
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}", exc_info=True)
            return []

    def delete_documents_by_source(self, source: str):
        try:
            self.collection.delete(where={"source": source})
            logger.info(
                f"已从集合 '{self.collection_name}' 中删除所有来源为 '{source}' 的文档。"
            )
        except Exception as e:
            logger.error(f"从向量数据库中删除文档时出错: {e}", exc_info=True)

vector_db = VectorDBClient()
