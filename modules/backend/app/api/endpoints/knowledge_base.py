from fastapi import APIRouter, HTTPException
from typing import List, Dict

from ...services.knowledge_base import kb_service

router = APIRouter()

@router.get("/documents", response_model=List[Dict[str, any]])
async def list_documents():
    """获取所有已上传的文档列表。"""
    documents = await kb_service.list_all_documents()
    if documents is None:
        raise HTTPException(status_code=500, detail="无法从知识库获取文档列表")
    return documents

@router.delete("/documents/{source_name}")
async def delete_document(source_name: str):
    """根据文件名删除知识库中的一个文档。"""
    success = await kb_service.delete_documents_by_source(source_name)
    if not success:
        raise HTTPException(status_code=500, detail=f"删除文档 '{source_name}' 失败")
    return {"message": f"文档 '{source_name}' 已成功删除"}
