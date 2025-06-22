import os
from fastapi import APIRouter, UploadFile, File
from ...core.grpc_client import grpc_client_manager
from ...core.settings import settings
from ..schemas.admin import ModelSwitchRequest
from ...services.model_store import list_models as list_available_models, switch_generation_model

router = APIRouter()

@router.post("/models/upload")
async def upload_model(file: UploadFile = File(...)):
    # 保存上传的模型文件到指定目录
    model_dir = settings.MODEL_DIR
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    file_path = os.path.join(model_dir, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return {"success": True, "message": f"模型 {file.filename} 上传成功"}

@router.post("/models/switch")
async def switch_model(request: ModelSwitchRequest):
    model_name = request.model_name
    if not model_name:
        return {"success": False, "message": "参数错误：缺少 model_name"}
    await grpc_client_manager.connect()
    try:
        success, message = await grpc_client_manager.switch_model(model_name, "generation")
        if success:
            switch_generation_model(model_name)
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": f"切换模型失败: {e}"}

@router.get("/models")
async def get_models():
    try:
        models = list_available_models()
        return models
    except Exception as e:
        return {
            "generation_models": [],
            "embedding_models": [],
            "current_generation_model": "",
            "current_embedding_model": "",
            "error": str(e),
        }

@router.get("/models/status")
async def get_model_status():
    # 与 /models 接口返回内容相同
    try:
        models = list_available_models()
        return models
    except Exception as e:
        return {"error": str(e)}
