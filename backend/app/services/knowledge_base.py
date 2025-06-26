import os
import shutil
from typing import List, Optional
from .embedding import embedding_model  # 新增

class KnowledgeBaseService:
    """
    简易本地知识库维护服务：支持文档上传、删除、列表、获取内容、转向量。
    支持未来与RAG/embedding联动。
    """

    def __init__(self, storage_dir: str = "./knowledge_base_docs"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def list_documents(self) -> List[str]:
        """列出知识库中所有文档名"""
        return [
            f for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """上传文档（覆盖同名）"""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return True

    def get_document(self, file_name: str) -> Optional[bytes]:
        """获取文档内容（可做预览/下载）"""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_document(self, file_name: str) -> bool:
        """删除指定文档"""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        return True

    def clear(self):
        """清空知识库（危险操作）"""
        shutil.rmtree(self.storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        return True

    # 新增：将指定文档转为embedding向量
    def embed_document(self, file_name: str):
        content_bytes = self.get_document(file_name)
        if content_bytes is None:
            return None
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("gbk", errors="ignore")
        embedding = embedding_model.embed(text)
        return embedding

kb_service = KnowledgeBaseService()
