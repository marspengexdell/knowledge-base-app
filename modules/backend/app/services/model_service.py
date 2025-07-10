import os
import shutil
from fastapi import UploadFile
from core.settings import settings
from .model_management import model_manager


class ModelService:
    def __init__(self, model_dir: str = settings.MODEL_DIR) -> None:
        self.model_dir = model_dir

    def list_models(self):
        return model_manager.list_models()

    async def switch_model(self, model_name: str, model_type: str = "generation"):
        # 当前仅支持生成模型切换，忽略 model_type
        return await model_manager.load_model(model_name)

    async def upload_model(self, file: UploadFile):
        if not file.filename.endswith(".gguf"):
            raise ValueError("只能上传 .gguf 格式的模型文件。")
        os.makedirs(self.model_dir, exist_ok=True)
        dest = os.path.join(self.model_dir, file.filename)
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return dest

from fastapi import UploadFile
import os
import json
from pathlib import Path
from core.grpc_client import grpc_client_manager
from core.settings import settings
from protos import inference_pb2


class ModelService:
    """Service for managing generation and embedding models."""

    def __init__(self) -> None:
        self.model_dir = Path(settings.MODEL_DIR)
        self.active_file = Path("/models/active_models.json")

    def upload_model(self, file: UploadFile) -> dict:
        """Save uploaded model file under the model directory."""
        if not (file.filename.endswith(".gguf") or file.filename.endswith(".safetensors")):
            return {"success": False, "message": "只允许上传 .gguf 或 .safetensors 文件"}
        self.model_dir.mkdir(parents=True, exist_ok=True)
        dest = self.model_dir / file.filename
        content = file.file.read()
        with open(dest, "wb") as f:
            f.write(content)
        return {"success": True, "message": f"模型 {file.filename} 上传成功"}

    def _load_active(self) -> dict:
        if self.active_file.exists():
            try:
                return json.loads(self.active_file.read_text())
            except Exception:
                pass
        return {"generation": "", "embedding": ""}

    def _save_active(self, data: dict) -> None:
        self.active_file.write_text(json.dumps(data))

    def list_models(self) -> dict:
        """Return available models and active model names."""
        generation_models = []
        embedding_models = []
        if self.model_dir.is_dir():
            for name in os.listdir(self.model_dir):
                if name.endswith(".gguf") or name.endswith(".safetensors"):
                    lower = name.lower()
                    if "embed" in lower or "embedding" in lower:
                        embedding_models.append(name)
                    else:
                        generation_models.append(name)
        active = self._load_active()
        return {
            "generation_models": generation_models,
            "embedding_models": embedding_models,
            "current_generation_model": active.get("generation", ""),
            "current_embedding_model": active.get("embedding", ""),
        }

    async def switch_model(self, model_name: str, model_type: inference_pb2.ModelType) -> tuple[bool, bool, str]:
        """Switch the running model via gRPC and update local active record.

        Returns a tuple (success, loading, message). 'loading' indicates the
        inference service is busy loading another model.
        """
        if not grpc_client_manager.stub:
            await grpc_client_manager.connect()
        success, message = await grpc_client_manager.switch_model(model_name, model_type)
        loading = message == "loading_busy"
        if success:
            active = self._load_active()
            if model_type == inference_pb2.ModelType.GENERATION:
                active["generation"] = model_name
            elif model_type == inference_pb2.ModelType.EMBEDDING:
                active["embedding"] = model_name
            self._save_active(active)
        return success, loading, message


model_service = ModelService()
