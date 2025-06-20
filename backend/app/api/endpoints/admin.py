import os
from fastapi import APIRouter, Form, HTTPException
from typing import Dict

router = APIRouter()

MODEL_DIR = "/models"  # 容器内模型目录，注意和 docker-compose 的挂载保持一致

# 临时记录当前模型，可替换为 DB/文件
CURRENT_MODEL_STATE = {
    "generation": "",
    "embedding": ""
}

@router.get("/models")
def get_models() -> Dict:
    files = os.listdir(MODEL_DIR)
    generation_models = [f for f in files if f.endswith(".gguf") or f.endswith(".safetensors")]
    embedding_models = [f for f in files if "embed" in f.lower()]  # 按需筛选
    return {
        "generation_models": generation_models,
        "embedding_models": embedding_models,
        "current_generation_model": CURRENT_MODEL_STATE["generation"],
        "current_embedding_model": CURRENT_MODEL_STATE["embedding"]
    }

@router.post("/models/switch")
def switch_model(model_name: str = Form(...), model_type: str = Form(...)):
    files = os.listdir(MODEL_DIR)
    if model_type == "generation":
        if model_name not in files:
            raise HTTPException(status_code=404, detail="模型不存在")
        CURRENT_MODEL_STATE["generation"] = model_name
        # 这里可以添加实际热加载/切换模型的代码
    elif model_type == "embedding":
        if model_name not in files:
            raise HTTPException(status_code=404, detail="模型不存在")
        CURRENT_MODEL_STATE["embedding"] = model_name
        # 这里可以添加实际热加载/切换 embedding 模型的代码
    else:
        raise HTTPException(status_code=400, detail="模型类型错误")
    return {"message": f"{model_type} 模型切换为 {model_name}"}