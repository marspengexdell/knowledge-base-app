from fastapi import APIRouter, Query, HTTPException
from services.knowledge_base import kb_service

router = APIRouter()


@router.get("/embed_doc")
async def embed_document_api(file_name: str = Query(...)):
    """输入知识库中的文件名，返回embedding向量"""
    try:
        result = await kb_service.embed_document(file_name)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
