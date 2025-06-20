from fastapi import APIRouter, HTTPException, Body
import requests
from app.core.config import settings

router = APIRouter()

INFERENCE_SERVER_URL = settings.INFERENCE_SERVER_URL or "http://inference:50051"

@router.get("/models", summary="列出可用模型")
def list_models():
    try:
        resp = requests.get(f"{INFERENCE_SERVER_URL}/api/models")
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理服务异常: {e}")

@router.post("/load-model", summary="加载/切换指定模型")
def load_model(model_name: str = Body(...), model_type: str = Body('generation')):
    try:
        resp = requests.post(
            f"{INFERENCE_SERVER_URL}/api/load",
            json={"model_name": model_name, "model_type": model_type}
        )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理服务异常: {e}")

@router.get("/model-status", summary="查询当前加载模型")
def model_status():
    try:
        resp = requests.get(f"{INFERENCE_SERVER_URL}/api/status")
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理服务异常: {e}")