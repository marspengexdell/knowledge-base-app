from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import logging

from ...services.knowledge_base import kb_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
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
