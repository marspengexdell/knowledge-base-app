

from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from core.grpc_client import grpc_client_manager
from protos import inference_pb2

from core.grpc_client import grpc_client_manager
from protos import inference_pb2

from fastapi import APIRouter, HTTPException, UploadFile, File, Body

from services.model_service import model_service


router = APIRouter()

@router.get("/")
async def list_models():
    """
    返回所有可用模型，直接返回 [{'model_name': ..., 'model_path': ..., 'active': True/False}]
    """
    try:

        models = await grpc_client_manager.list_models()
        return models

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/{model_name}")
async def load_model(model_name: str, model_type: str = Body("generation")):
    """
    触发加载指定模型，返回是否成功和消息
    """
    try:
        if model_type.lower() == "embedding":
            model_enum = inference_pb2.ModelType.EMBEDDING
        else:
            model_enum = inference_pb2.ModelType.GENERATION

        success, loading, msg = await model_service.switch_model(model_name, model_enum)

        if not success:
            if loading:
                raise HTTPException(status_code=202, detail="模型正在加载，请稍后再试。")
            raise HTTPException(status_code=500, detail=msg or "切换模型失败")
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
