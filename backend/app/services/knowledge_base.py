import os
import shutil
import logging
from typing import List, Optional
import chromadb  # pip install chromadb-client
from .embedding import embedding_model

# ========== 目录和环境变量对齐 ==========
STORAGE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "/app/app/knowledge_base_docs")
CHROMA_HOST = os.getenv("VECTOR_DB_HOST", "vector-db")
CHROMA_PORT = int(os.getenv("VECTOR_DB_PORT", 8000))
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name="knowledge_base")

# ========== 日志 ==========
logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    本地知识库服务，集成文档存储+向量化+ChromaDB向量检索。
    """
    def __init__(self, storage_dir: str = STORAGE_DIR):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """上传文档（保存本地+向量化存入Chroma）"""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        try:
            text_content = file_data.decode("utf-8")
        except UnicodeDecodeError:
            text_content = file_data.decode("gbk", errors="ignore")
        embedding = embedding_model.embed(text_content)[0]
        collection.add(
            embeddings=[embedding],
            documents=[text_content],
            metadatas=[{"source": file_name}],
            ids=[file_name]
        )
        return True

    def embed_document(self, file_name: str):
        """
        Reads a document from storage, embeds its content via the inference service,
        and stores the resulting vector in the ChromaDB.
        """
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            logger.error(f"Document not found for embedding: {file_name}")
            raise FileNotFoundError(f"Document '{file_name}' not found in knowledge base.")

        logger.info(f"Reading document {file_name} for embedding.")
        with open(file_path, "rb") as f:
            file_data = f.read()

        try:
            text_content = file_data.decode("utf-8")
        except UnicodeDecodeError:
            text_content = file_data.decode("gbk", errors="ignore")

        logger.info(f"Sending content of {file_name} to embedding model.")
        embeddings = embedding_model.embed(text_content)

        collection.add(
            embeddings=[embeddings[0]],  # embed() returns a list, we take the first element
            documents=[text_content],
            metadatas=[{"source": file_name}],
            ids=[file_name]
        )
        logger.info(f"Successfully embedded and stored document: {file_name}")
        return {"message": f"Successfully embedded document: {file_name}"}

    def search(self, query: str, n_results: int = 2) -> List[str]:
        embedding = embedding_model.embed(query)[0]
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        return results.get("documents", [[]])[0]

    def list_documents(self) -> List[str]:
        return [
            f for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    def get_document(self, file_name: str) -> Optional[bytes]:
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_document(self, file_name: str) -> bool:
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        try:
            collection.delete(ids=[file_name])
        except Exception:
            pass
        return True

    def clear(self):
        shutil.rmtree(self.storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        collection.delete(where={})  # 删除所有

# 单例实例，供全局调用
kb_service = KnowledgeBaseService()
