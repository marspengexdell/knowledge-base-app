from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import logging

from services.knowledge_base import kb_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """import os
import logging
import io
import pdfplumber
from pathlib import Path
from docx import Document

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.storage_dir = "storage/documents"
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        self.docs = {}

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        suffix = filename.lower().split('.')[-1]
        if suffix in ["txt", "md"]:
            return file_bytes.decode("utf-8", errors="ignore")

        elif suffix == "pdf":
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return "\n".join([page.extract_text() or "" for page in pdf.pages])

        elif suffix == "docx":
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs])

        else:
            raise ValueError("不支持的文件类型")

    def add_document(self, filename: str, file_bytes: bytes):
        # 保存原始文件
        file_path = os.path.join(self.storage_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # 提取文本（关键改造）
        try:
            text = self.extract_text(file_bytes, filename)
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            raise RuntimeError(f"不支持或解析失败的文件: {e}")

        # 保存到内存（用于 embed）
        self.docs[filename] = text

    def list_documents(self):
        return list(self.docs.keys())

    def delete_document(self, filename: str) -> bool:
        path = os.path.join(self.storage_dir, filename)
        if os.path.exists(path):
            os.remove(path)
        return self.docs.pop(filename, None) is not None

    async def embed_document(self, filename: str):
        # 假设调用 embedding 向量存储接口
        from core.embedding import embed_text  # 伪代码
        text = self.docs.get(filename)
        if not text:
            raise RuntimeError("找不到文档内容")
        await embed_text(filename, text)


kb_service = KnowledgeBaseService()

    接收上传的文档，保存后立即进行向量化处理。
    """
    try:
        # 步骤 1: 将文件保存到本地
        # 这一步是为了持久化原始文件，方便未来管理
        file_data = await file.read()
        kb_service.add_document(file.filename, file_data)
        logger.info(f"文档 '{file.filename}' 已成功保存。")

        # 步骤 2: (核心改动) 立即对刚刚上传的文件进行向量化处理
        logger.info(f"正在对文档 '{file.filename}' 进行学习（向量化）...")
        await kb_service.embed_document(file.filename)
        logger.info(f"文档 '{file.filename}' 学习完成！")

        return {"success": True, "message": f"文件 '{file.filename}' 上传并学习成功！"}

    except Exception as e:
        logger.error(f"处理文件 '{file.filename}' 时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理文件失败: {e}")


@router.get("/list")
async def list_documents():
    docs = kb_service.list_documents()
    return {"docs": docs}


@router.get("/download")
async def download_document(file: str):
    file_path = os.path.join(kb_service.storage_dir, file)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=file)


@router.delete("/delete")
async def delete_document(file: str):
    success = kb_service.delete_document(file)
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {"success": True}
