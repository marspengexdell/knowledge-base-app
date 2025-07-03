from fastapi import APIRouter, UploadFile, File, HTTPException
from services.knowledge_base import kb_service

router = APIRouter()

@router.get("/documents")
async def list_documents():
    """列出所有知识库中的文档。"""
    docs = await kb_service.list_all_documents()
    return docs or []

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传并学习（向量化）一个新文档。
    """
    try:
        data = await file.read()
        kb_service.add_document(file.filename, data)
        await kb_service.embed_document(file.filename)
        return {"success": True, "message": f"文档 '{file.filename}' 上传并学习完成！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")

@router.delete("/documents/{source_name}")
async def delete_document(source_name: str):
    """
    删除指定文档（从文件夹和向量库一并移除）。
    """
    ok = await kb_service.delete_documents_by_source(source_name)
    if not ok:
        raise HTTPException(status_code=500, detail=f"删除文档 '{source_name}' 失败")
    return {"success": True, "message": f"文档 '{source_name}' 已成功删除"}
