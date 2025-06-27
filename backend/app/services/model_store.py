import json
import os
from pathlib import Path

MODEL_DIR = "/models"
# Shared file storing the currently selected generation and embedding models.
# It is mounted into both the backend and inference containers.
ACTIVE_MODELS_FILE = Path("/models/active_models.json")

def _ensure_file():
    if not ACTIVE_MODELS_FILE.exists():
        ACTIVE_MODELS_FILE.write_text(json.dumps({"generation": "", "embedding": ""}))

def _load_active() -> dict:
    _ensure_file()
    try:
        return json.loads(ACTIVE_MODELS_FILE.read_text())
    except Exception:
        return {"generation": "", "embedding": ""}

def _save_active(data: dict) -> None:
    ACTIVE_MODELS_FILE.write_text(json.dumps(data))

def list_models() -> dict:
    """Return available models and current active models."""
    generation_models = []
    embedding_models = []
    if os.path.isdir(MODEL_DIR):
        for name in os.listdir(MODEL_DIR):
            if name.endswith(".gguf") or name.endswith(".safetensors"):
                lower = name.lower()
                if "embed" in lower or "embedding" in lower:
                    embedding_models.append(name)
                else:
                    generation_models.append(name)
        embed_dir = os.path.join(MODEL_DIR, "embedding-model")
        if os.path.isdir(embed_dir):
            for sub in os.listdir(embed_dir):
                sub_path = os.path.join(embed_dir, sub)
                # 新增：支持 huggingface 目录（如 bge-base-zh 文件夹）
                if os.path.isdir(sub_path):
                    embedding_models.append(os.path.join("embedding-model", sub))
                # 兼容：也支持单独的 .gguf/.safetensors 文件
                elif sub.endswith(".gguf") or sub.endswith(".safetensors"):
                    embedding_models.append(os.path.join("embedding-model", sub))
    active = _load_active()
    return {
        "generation_models": generation_models,
        "embedding_models": embedding_models,
        "current_generation_model": active.get("generation", ""),
        "current_embedding_model": active.get("embedding", ""),
    }

def switch_generation_model(model_name: str) -> bool:
    """Set the active generation model if it exists."""
    models = list_models()
    if model_name not in models["generation_models"]:
        return False
    active = _load_active()
    active["generation"] = model_name
    _save_active(active)
    return True

def switch_embedding_model(model_name: str) -> bool:
    """Set the active embedding model if it exists."""
    models = list_models()
    if model_name not in models["embedding_models"]:
        return False
    active = _load_active()
    active["embedding"] = model_name
    _save_active(active)
    return True
