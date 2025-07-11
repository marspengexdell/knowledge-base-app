from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from services.knowledge_service import knowledge_service

router = APIRouter()

@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str = Query("", description="搜索关键词"),
    by: str = Query("all", regex="^(title|content|all)$")
):
    return await knowledge_service.paginated_list(page, page_size, search, by)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        data = await file.read()
        doc_id = knowledge_service.add_document(file.filename, data)
        await knowledge_service.embed_document(doc_id, file.filename)
        return {"success": True, "message": f"文档 '{file.filename}' 上传成功", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    if not doc_id or doc_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid document ID")
    success = await knowledge_service.delete_documents_by_id(doc_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"删除失败: ID {doc_id}")
    return {"success": True, "message": f"文档已删除: {doc_id}"}
