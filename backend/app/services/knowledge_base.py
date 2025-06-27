import os
import shutil
from typing import List, Optional
import chromadb  # pip install chromadb-client
from .embedding import embedding_model

# 读取 ChromaDB 配置（用 docker-compose 的环境变量，默认端口8000 注意不是8001）
CHROMA_HOST = os.getenv("VECTOR_DB_HOST", "vector-db")
CHROMA_PORT = int(os.getenv("VECTOR_DB_PORT", 8000))
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name="knowledge_base")

class KnowledgeBaseService:
    """
    本地知识库服务，集成文档存储+向量化+ChromaDB向量检索。
    """

    def __init__(self, storage_dir: str = "./knowledge_base_docs"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """上传文档（保存本地+向量化存入Chroma）"""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)

        # 文本解码
        try:
            text_content = file_data.decode("utf-8")
        except UnicodeDecodeError:
            text_content = file_data.decode("gbk", errors="ignore")

        # 向量化
        embedding = embedding_model.embed(text_content)[0]  # 返回二维数组，取第一个
        # 存入 Chroma
        collection.add(
            embeddings=[embedding],
            documents=[text_content],
            metadatas=[{"source": file_name}],
            ids=[file_name]
        )
        return True

    def search(self, query: str, n_results: int = 2) -> List[str]:
        """用向量检索知识库，返回最相关文档内容列表"""
        embedding = embedding_model.embed(query)[0]
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        # 返回所有检索到的文档文本
        return results.get("documents", [[]])[0]

    def list_documents(self) -> List[str]:
        """列出知识库中所有文档名"""
        return [
            f for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    def get_document(self, file_name: str) -> Optional[bytes]:
        """获取文档内容（可做预览/下载）"""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_document(self, file_name: str) -> bool:
        """删除指定文档，并从ChromaDB中删除"""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        # Chroma删除
        try:
            collection.delete(ids=[file_name])
        except Exception:
            pass
        return True

    def clear(self):
        """清空知识库（危险操作）"""
        shutil.rmtree(self.storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        # 删除所有ChromaDB中的记录
        collection.delete(where={})  # 删除所有

kb_service = KnowledgeBaseService()
