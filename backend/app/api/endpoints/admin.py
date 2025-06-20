import os
import shutil
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from typing import Dict, List

router = APIRouter()

# 注意这里路径要和 docker-compose.yaml 挂载一致
MODEL_DIR = "/models"

# 简单的内存状态记录（可替换为 DB/文件/redis）
CURRENT_MODEL_STATE = {
    "generation": "",
    "embedding": ""
}

def scan_models() -> Dict[str, List[str]]:
    """扫描模型目录并区分类型"""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        return {"generation_models": [], "embedding_models": []}
    files = os.listdir(MODEL_DIR)
    generation_models = []
    embedding_models = []
    for f in files:
        # 支持多种模型后缀
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

    # 这里可以通过RPC/消息队列通知gRPC服务热加载模型（可扩展）
    return {"message": f"{model_type} 模型切换为 {model_name}"}

@router.post("/models/upload")
async def upload_model(file: UploadFile = File(...)):
    """
    上传新模型文件（支持 .gguf 和 .safetensors）
    """
    if not (file.filename.endswith(".gguf") or file.filename.endswith(".safetensors")):
        raise HTTPException(status_code=400, detail="只允许上传 .gguf 或 .safetensors 文件")
    file_path = os.path.join(MODEL_DIR, file.filename)
    # 避免覆盖同名文件
    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail="同名模型文件已存在")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "模型上传成功", "filename": file.filename}
