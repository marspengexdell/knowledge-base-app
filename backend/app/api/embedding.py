from fastapi import APIRouter, Query
from app.services.knowledge_base import kb_service

router = APIRouter()

@router.get("/embed_doc")
def embed_document_api(file_name: str = Query(...)):
    """输入知识库中的文件名，返回embedding向量"""
    result = kb_service.embed_document(file_name)
    if result is None:
        return {"error": "file not found"}
    return {"embedding": result}
