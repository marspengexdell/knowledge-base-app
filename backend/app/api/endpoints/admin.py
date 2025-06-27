import os
from fastapi import APIRouter, UploadFile, File
from ...core.grpc_client import grpc_client_manager
from ...core.settings import settings
from ..schemas.admin import ModelSwitchRequest
from ...services.model_store import switch_generation_model, switch_embedding_model
from ...protos import inference_pb2

router = APIRouter()

@router.post("/models/upload")
async def upload_model(file: UploadFile = File(...)):
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
    model_type_str = request.model_type.upper()  # "GENERATION" or "EMBEDDING"
    model_type_enum = inference_pb2.ModelType.Value(request.model_type)

    if not model_name:
        return {"success": False, "message": "参数错误：缺少 model_name"}
    if not grpc_client_manager.stub:
        await grpc_client_manager.connect()
    try:
        success, message = await grpc_client_manager.switch_model(model_name, model_type_enum)
        # 支持嵌入模型和生成模型的本地状态持久化
        if success:
            if model_type_str == "GENERATION":
                switch_generation_model(model_name)
            elif model_type_str == "EMBEDDING":
                switch_embedding_model(model_name)
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": f"切换模型失败: {e}"}

@router.get("/models")
async def get_models():
    try:
        await grpc_client_manager.connect()
        models = await grpc_client_manager.list_models()
        return models
    except Exception as e:
        try:
            from ...services.model_store import list_models as list_available_models
            models = list_available_models()
            models["device"] = ""
            return models
        except Exception:
            return {
                "generation_models": [],
                "embedding_models": [],
                "current_generation_model": "",
                "current_embedding_model": "",
                "device": "",
                "error": str(e),
            }

@router.get("/models/status")
async def get_model_status():
    try:
        await grpc_client_manager.connect()
        models = await grpc_client_manager.list_models()
        return models
    except Exception as e:
        try:
            from ...services.model_store import list_models as list_available_models
            models = list_available_models()
            models["device"] = ""
            return models
        except Exception:
            return {"error": str(e)}
