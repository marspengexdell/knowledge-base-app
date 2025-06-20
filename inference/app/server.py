import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from services.model_service import ModelService

# 初始化模型服务，模型目录用挂载的 /app/models
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")
model_service = ModelService(MODEL_DIR)

app = FastAPI()

@app.get("/api/models")
def list_models():
    """
    获取所有可用模型列表，分 generation/embedding 分类
    """
    return model_service.list_models()

@app.post("/api/load")
def load_model(model_name: str, model_type: str = 'generation'):
    """
    动态加载模型（热切换），支持 generation/embedding
    """
    ok = model_service.load_model(model_name, model_type)
    if not ok:
        raise HTTPException(status_code=400, detail="模型加载失败")
    return {"msg": "模型已加载", "current_model": model_name, "type": model_type}

@app.get("/api/status")
def status():
    """
    查看当前加载的模型状态
    """
    return model_service.status()

@app.post("/api/generate")
def generate(prompt: str, model_name: str = None):
    """
    文本生成接口，支持临时切换模型
    """
    result = model_service.generate(prompt, model_name)
    return {"result": result}

@app.post("/api/embed")
def embed(text: str, model_name: str = None):
    """
    文本向量化接口，支持临时切换 embedding 模型
    """
    result = model_service.embed(text, model_name)
    return {"embedding": result}

# 下面是 gRPC 服务器启动的部分（用 gunicorn/多进程可选，或你原来的 proto 实现）

if __name__ == "__main__":
    # FastAPI 启动，生产用 gunicorn/uvicorn
    uvicorn.run(app, host="0.0.0.0", port=50051)
