import os
import logging
from typing import List, Optional
import chromadb
from .embedding import embedding_model
import asyncio # 【新增】导入asyncio

# ... (常量定义) ...
STORAGE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "/app/knowledge_base_storage")
CHROMA_HOST = os.getenv("VECTOR_DB_HOST", "vector-db")
CHROMA_PORT = int(os.getenv("VECTOR_DB_PORT", 8000))
try:
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = chroma_client.get_or_create_collection(name="knowledge_base")
except Exception as e:
    logging.error(f"无法连接到ChromaDB: {e}", exc_info=True)
    chroma_client = None
    collection = None

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, storage_dir: str = STORAGE_DIR):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    # 【修改】上传文档只负责保存文件，不再做嵌入
    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """仅将文档保存到本地磁盘"""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"文档 '{file_name}' 已保存到本地。")
        return True

    # 【修改】embed_document 实现分块和批量嵌入
    async def embed_document(self, file_name: str):
        """读取文档，分块，然后批量嵌入并存入ChromaDB。"""
        if collection is None: raise ConnectionError("ChromaDB not connected.")
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            logger.error(f"无法找到待嵌入的文档: {file_name}")
            raise FileNotFoundError(f"Document '{file_name}' not found.")

        logger.info(f"正在读取并为文档 '{file_name}' 分块...")
        with open(file_path, "rb") as f:
            file_data = f.read()

        try:
            text_content = file_data.decode("utf-8")
        except UnicodeDecodeError:
            text_content = file_data.decode("gbk", errors="ignore")

        chunk_size = 500
        chunk_overlap = 50
        text_chunks = [text_content[i:i + chunk_size] for i in range(0, len(text_content), chunk_size - chunk_overlap)]
        if not text_chunks:
            logger.warning(f"文档 '{file_name}' 为空，无法分块。")
            return {"message": "Document is empty."}
        
        logger.info(f"文档已切分为 {len(text_chunks)} 个块。正在调用嵌入服务...")
        
        # 【修改】调用异步的 embed_batch
        embeddings = await embedding_model.embed_batch(text_chunks)
        if not embeddings or not any(embeddings):
            raise Exception("Embedding service returned empty results.")

        chunk_ids = [f"{file_name}-chunk-{i}" for i in range(len(text_chunks))]
        collection.add(
            embeddings=embeddings,
            documents=text_chunks,
            metadatas=[{"source": file_name} for _ in text_chunks],
            ids=chunk_ids
        )
        
        logger.info(f"成功为文档 '{file_name}' 嵌入并存储了 {len(text_chunks)} 个块。")
        return {"message": f"Successfully embedded {len(text_chunks)} chunks for document: {file_name}"}
        
    # 【修改】search 方法也改为异步
    async def search(self, query: str, n_results: int = 3) -> List[str]:
        if collection is None: raise ConnectionError("ChromaDB not connected.")
        if not query.strip(): return []
        
        query_embedding = await embedding_model.embed(query)
        if not query_embedding: return []
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results.get("documents", [[]])[0]

    # ... (list_documents, get_document, delete_document 等保持不变或做微调) ...
    def list_documents(self) -> List[str]:
        return [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]

    def get_document(self, file_name: str) -> Optional[bytes]:
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path): return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_document(self, file_name: str) -> bool:
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path): return False
        os.remove(file_path)
        try:
            if collection:
                # 删除所有与该文件名相关的块
                collection.delete(where={"source": file_name})
        except Exception as e:
            logger.error(f"从ChromaDB删除文档块时出错: {e}")
            pass
        return True

# 注意：因为方法变成了异步，外部调用需要调整。
# 单例实例保持不变
kb_service = KnowledgeBaseService()