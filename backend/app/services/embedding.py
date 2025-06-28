import json
import logging
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import threading


logger = logging.getLogger(__name__)

class EmbeddingModel:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, model_name_or_path="BAAI/bge-base-zh-v1.5"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.initialized = False
        return cls._instance

    def _resolve_model_path(self, default):
        env_model = os.getenv("EMBEDDING_MODEL")
        if env_model:
            path = Path(env_model)
            if not path.is_absolute():
                path = Path("/models") / env_model
            return path

        active_file = Path("/models/active_models.json")
        if active_file.exists():
            try:
                data = json.loads(active_file.read_text())
                model_name = data.get("embedding")
                if model_name:
                    path = Path(model_name)
                    if not path.is_absolute():
                        path = Path("/models") / model_name
                    return path
            except Exception as e:
                logger.error("Failed to read active embedding model: %s", e)
        return Path(default)

    def __init__(self, model_name_or_path="BAAI/bge-base-zh-v1.5"):
        if getattr(self, "initialized", False):
            return
        self.model = None
        resolved = self._resolve_model_path(model_name_or_path)
        self.model_name_or_path = str(resolved) if resolved else None

        if self.model_name_or_path and Path(self.model_name_or_path).exists():
            try:
                self.model = SentenceTransformer(self.model_name_or_path)
                logger.info("Loaded embedding model from %s", self.model_name_or_path)
            except Exception as e:
                logger.error("Error loading embedding model from %s: %s", self.model_name_or_path, e)
        else:
            logger.error("Embedding model path %s not found", self.model_name_or_path)

        if self.model is None:
            logger.warning("Embedding features disabled; no model loaded")
        self.initialized = True

    def embed(self, texts):
        if not self.model:
            logger.warning("Embedding requested but no model is loaded")
            return []
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True).tolist()

embedding_model = EmbeddingModel()
