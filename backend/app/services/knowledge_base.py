# backend/app/services/knowledge_base.py

import os
import shutil
from typing import List, Optional

class KnowledgeBaseService:
    """
    简易本地知识库维护服务：支持文档上传、删除、列表、获取内容。
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

# 单例对象，便于 import 复用
kb_service = KnowledgeBaseService()

# FastAPI 路由建议（可选）
# from fastapi import APIRouter, File, UploadFile
# router = APIRouter()
# @router.post("/upload")
# async def upload_doc(file: UploadFile = File(...)):
#     kb_service.add_document(file.filename, await file.read())
#     return {"success": True}
