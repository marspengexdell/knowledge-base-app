import os
import logging
import chromadb
from langchain_core.documents import Document
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class VectorDBClient:
    """
    一个专门用于与Chroma向量数据库交互的客户端。
    它封装了连接、添加、搜索和删除文档的所有底层逻辑。
    """
    def __init__(self):
        # 从环境变量获取ChromaDB的URL，如果获取不到则使用默认值
        db_url_str = os.getenv("VECTOR_DB_URL", "http://vector-db:8000")
        logger.info(f"正在连接到向量数据库: {db_url_str}")

        try:
            # --- 代码修复开始 ---
            # 解析 URL 以分离出 host 和 port
            parsed_url = urlparse(db_url_str)
            db_host = parsed_url.hostname
            db_port = parsed_url.port

            if not db_host or not db_port:
                raise ValueError("无效的 VECTOR_DB_URL，无法解析 host 或 port")

            # 初始化ChromaDB HTTP客户端
            # 使用新的 host 和 port 参数
            self.client = chromadb.HttpClient(
                host=db_host,
                port=db_port,
                settings=chromadb.Settings(
                    is_persistent=True,
                )
            )
            # --- 代码修复结束 ---
            
            # 定义一个统一的集合名称，所有文档都将存储在这里
            self.collection_name = "knowledge_base_main_collection"
            
            # 获取或创建这个集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            logger.info(f"成功连接到向量数据库，并获取/创建集合: '{self.collection_name}'")
        except Exception as e:
            logger.error(f"连接向量数据库失败: {e}", exc_info=True)
            # 如果连接失败，抛出异常以阻止服务启动
            raise

    async def add_documents(self, documents: List[Document], embeddings: List[List[float]], document_source: str):
        """
        将一批文档片段及其对应的向量化结果添加到数据库。
        """
        try:
            # 为每个文档片段创建唯一的ID和元数据
            ids = [f"{document_source}_{i}" for i in range(len(documents))]
            metadatas = [{'source': document_source, 'text': doc.page_content} for doc in documents]
            
            # 使用 collection.add() 方法一次性添加所有数据
            self.collection.add(
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"成功向集合 '{self.collection_name}' 中添加了 {len(documents)} 个文档片段，来源: {document_source}。")
        except Exception as e:
            logger.error(f"添加文档到向量数据库时出错: {e}", exc_info=True)

    async def search_with_vector(self, query_embedding: List[float], top_k: int) -> List[Document]:
        """
        使用一个给定的查询向量，在数据库中执行相似度搜索。
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding], # 使用预先计算好的向量进行搜索
                n_results=top_k
            )
            
            # 将搜索结果格式化为LangChain的Document对象列表
            found_docs = []
            if results and results.get('documents') and results['documents'][0]:
                for i, text in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    distance = results['distances'][0][i] if results.get('distances') else None
                    metadata['distance'] = distance
                    found_docs.append(Document(page_content=text, metadata=metadata))

            logger.info(f"通过向量搜索找到了 {len(found_docs)} 个相关文档。")
            return found_docs
        except Exception as e:
            logger.error(f"在向量数据库中通过向量搜索时出错: {e}", exc_info=True)
            return []

    def delete_documents_by_source(self, source: str):
        """
        根据文档源（文件名）删除所有相关的文档片段。
        """
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"已从集合 '{self.collection_name}' 中删除所有来源为 '{source}' 的文档。")
        except Exception as e:
            logger.error(f"从向量数据库中删除文档时出错: {e}", exc_info=True)


# 创建一个全局的向量数据库客户端单例，供项目其他模块导入和使用
vector_db = VectorDBClient()
