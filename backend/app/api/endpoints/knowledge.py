from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os

from ...services.knowledge_base import kb_service

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        data = await file.read()
        kb_service.add_document(file.filename, data)
        return {"success": True, "message": "文件上传成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
