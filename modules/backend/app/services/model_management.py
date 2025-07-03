import os
import logging
from typing import List, Dict, Optional, Tuple
from core.grpc_client import grpc_client_manager
from protos import inference_pb2
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models_dir = "/models"  # Directory where models are stored
        self.grpc_client_manager = grpc_client_manager
        self.embedding_model: Optional[SentenceTransformer] = None
        self.current_model_name = ""
        logger.info("ModelManager initialized. Model discovery will be dynamic.")

    def _discover_supported_models(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory '{self.models_dir}' not found.")
            return []
        models_list = []
        try:
            for filename in os.listdir(self.models_dir):
                if filename.endswith(".gguf"):
                    model_path = os.path.join(self.models_dir, filename)
                    models_list.append(
                        {"model_name": filename, "model_path": model_path}
                    )
        except Exception as e:
            logger.error(
                f"Error while scanning models directory '{self.models_dir}': {e}",
                exc_info=True,
            )
            return []
        logger.info(f"Discovered {len(models_list)} supported models in this scan.")
        return models_list

    def list_models(self) -> List[Dict[str, str]]:
        logger.info("Dynamically scanning for models...")
        model_list = self._discover_supported_models()
        # 标记激活模型
        for m in model_list:
            m["active"] = (m["model_name"] == self.current_model_name)
        return model_list

    def get_model_path(self, model_name: str) -> Optional[str]:
        for model_info in self._discover_supported_models():
            if model_info["model_name"] == model_name:
                return model_info["model_path"]
        logger.warning(f"Model '{model_name}' not found in '{self.models_dir}'.")
        return None

    async def load_model(self, model_name: str) -> Tuple[bool, str]:
        model_path = self.get_model_path(model_name)
        logger.info(f"load_model called, model_name={model_name}, model_path={model_path}")
        if not model_path:
            logger.error(f"Model file not found for {model_name}")
            return False, f"Model file not found: {model_name}"
        try:
            success, msg = await self.grpc_client_manager.switch_model(
                model_name, inference_pb2.ModelType.GENERATION
            )
            logger.info(f"switch_model grpc response: success={success}, msg={msg}")
            if success:
                self.current_model_name = model_name
            # 特殊处理 loading_busy
            if msg == "loading_busy":
                logger.warning(f"模型正在加载: {model_name}")
                return False, "模型正在加载，请稍后再试。"
            return success, msg
        except Exception as e:
            logger.error(f"gRPC 切换模型异常: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    def is_embedding_model_loaded(self) -> bool:
        return self.embedding_model is not None

    async def get_embedding_model(self) -> Optional[SentenceTransformer]:
        if self.embedding_model:
            return self.embedding_model
        try:
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            logger.info(f"Loading embedding model: {model_name}...")
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully.")
            return self.embedding_model
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            self.embedding_model = None
            return None

model_manager = ModelManager()
