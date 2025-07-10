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


model_service = ModelService()
