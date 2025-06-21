import os
import shutil
import re
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from typing import Dict, List

router = APIRouter()

MODEL_DIR = "/models"

CURRENT_MODEL_STATE = {
    "generation": "",
    "embedding": ""
}

SAFE_MODEL_NAME = re.compile(r'^[\w\-.]+$')

def scan_models() -> Dict[str, List[str]]:
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        return {"generation_models": [], "embedding_models": []}
    files = os.listdir(MODEL_DIR)
    generation_models, embedding_models = [], []
    for f in files:
        if f.endswith((".gguf", ".safetensors")):
            lower = f.lower()
            if "embed" in lower or "embedding" in lower:
                embedding_models.append(f)
            else:
                generation_models.append(f)
    return {
        "generation_models": generation_models,
        "embedding_models": embedding_models,
    }

@router.get("/models")
def get_models() -> Dict:
    """
    获取模型列表和当前激活模型
    """
    models = scan_models()
    return {
        "generation_models": models["generation_models"],
        "embedding_models": models["embedding_models"],
        "current_generation_model": CURRENT_MODEL_STATE["generation"],
        "current_embedding_model": CURRENT_MODEL_STATE["embedding"],
    }

@router.post("/models/switch")
def switch_model(
    model_name: str = Form(...),
    model_type: str = Form(...)
):
    """
    切换当前激活模型（只是标记，实际热加载由gRPC服务做）
    """
    models = scan_models()
    if not SAFE_MODEL_NAME.match(model_name):
        raise HTTPException(status_code=400, detail="非法模型文件名")
    if model_type == "generation":
        if model_name not in models["generation_models"]:
            raise HTTPException(status_code=404, detail="生成模型不存在")
        CURRENT_MODEL_STATE["generation"] = model_name
    elif model_type == "embedding":
        if model_name not in models["embedding_models"]:
            raise HTTPException(status_code=404, detail="嵌入模型不存在")
        CURRENT_MODEL_STATE["embedding"] = model_name
    else:
        raise HTTPException(status_code=400, detail="模型类型错误")
    return {"message": f"{model_type} 模型切换为 {model_name}"}

@router.post("/models/upload")
async def upload_model(file: UploadFile = File(...)):
    """
    上传新模型文件（支持 .gguf 和 .safetensors）
    """
    if not (file.filename.endswith(".gguf") or file.filename.endswith(".safetensors")):
        raise HTTPException(status_code=400, detail="只允许上传 .gguf 或 .safetensors 文件")
    if not SAFE_MODEL_NAME.match(file.filename):
        raise HTTPException(status_code=400, detail="非法模型文件名，仅允许英文字母、数字、下划线、点和短横线")
    file_path = os.path.join(MODEL_DIR, file.filename)
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=409,
            detail=f"同名模型文件已存在（{file.filename}）"
        )
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型保存失败: {str(e)}")
    return {"message": "模型上传成功", "filename": file.filename}
