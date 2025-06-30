from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from services.model_management import model_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_model_file(file: UploadFile = File(...)):
    """
    接收并保存上传的模型文件。
    """
    try:
        file_data = await file.read()
        model_service.add_model(file.filename, file_data)
        return {"success": True, "filename": file.filename, "message": "模型上传成功！"}
    except Exception as e:
        logger.error(f"上传模型文件 '{file.filename}' 时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传模型失败: {e}")

@router.get("/list")
async def list_available_models():
    """
    获取已上传的模型列表。
    """
    try:
        models = model_service.list_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"获取模型列表时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {e}")
