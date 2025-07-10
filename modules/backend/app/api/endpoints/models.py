from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from services.model_service import model_service

router = APIRouter()

@router.get("/")
async def list_models():
    """
    返回所有可用模型，直接返回 [{'model_name': ..., 'model_path': ..., 'active': True/False}]
    """
    try:
        return model_service.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/{model_name}")
async def load_model(model_name: str, model_type: str = Body("generation")):
    """
    触发加载指定模型，返回是否成功和消息
    """
    try:
        success, msg = await model_service.switch_model(model_name, model_type)
        if not success:
            # 判断“模型正在加载”，用 202 而不是 500
            if "正在加载" in (msg or ""):
                raise HTTPException(status_code=202, detail=msg)
            raise HTTPException(
                status_code=500,
                detail=msg or f"Model '{model_name}' not found or failed to load.",
            )
        return {"success": True, "message": f"Model '{model_name}' 已切换"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    """
    上传新模型文件到 /models 目录
    """
    try:
        await model_service.upload_model(file)
        return {"success": True, "message": f"模型 {file.filename} 上传成功!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
