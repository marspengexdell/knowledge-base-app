import os
import logging
from typing import List, Dict, Optional
from core.grpc_client import grpc_client_manager
from protos import inference_pb2
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages discovering, loading, and interacting with AI models.
    This version dynamically scans for models upon request.
    """

    def __init__(self):
        """Initializes the ModelManager."""
        self.models_dir = "/models"  # Directory where models are stored
        self.grpc_client_manager = grpc_client_manager
        self.embedding_model: Optional[SentenceTransformer] = None
        logger.info("ModelManager initialized. Model discovery will be dynamic.")

    def _discover_supported_models(self) -> List[Dict[str, str]]:
        """
        Scans the models directory to find all supported .gguf model files.
        """
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory '{self.models_dir}' not found.")
            return []

        models_list = []
        try:
            for filename in os.listdir(self.models_dir):
                if filename.endswith(".gguf"):
                    model_path = os.path.join(self.models_dir, filename)
                    models_list.append({
                        "model_name": filename,
                        "model_path": model_path
                    })
        except Exception as e:
            logger.error(f"Error while scanning models directory '{self.models_dir}': {e}", exc_info=True)
            return []

        logger.info(f"Discovered {len(models_list)} supported models in this scan.")
        return models_list

    def list_models(self) -> List[Dict[str, str]]:
        """Returns a fresh list of discovered models by scanning the directory now."""
        logger.info("Dynamically scanning for models...")
        return self._discover_supported_models()

    def get_model_path(self, model_name: str) -> Optional[str]:
        """Finds the full path of a model by its name by performing a fresh scan."""
        for model_info in self._discover_supported_models():
            if model_info['model_name'] == model_name:
                return model_info['model_path']
        logger.warning(f"Model '{model_name}' not found in '{self.models_dir}'.")
        return None

    async def load_model(self, model_name: str) -> bool:
        """Request the inference service to switch to the specified model."""
        model_path = self.get_model_path(model_name)
        if not model_path:
            return False
        success, _ = await self.grpc_client_manager.switch_model(
            model_name, inference_pb2.ModelType.GENERATION
        )
        return success

    def is_embedding_model_loaded(self) -> bool:
        """Checks if the embedding model has been loaded into memory."""
        return self.embedding_model is not None

    async def get_embedding_model(self) -> Optional[SentenceTransformer]:
        """
        Loads and returns the embedding model. If already loaded, returns the existing instance.
        """
        if self.embedding_model:
            return self.embedding_model

        try:
            # For now, we use a hardcoded, well-known embedding model.
            # This could be made configurable in the future.
            model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
            logger.info(f"Loading embedding model: {model_name}...")
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully.")
            return self.embedding_model
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            self.embedding_model = None
            return None

# Create a single, shared instance of the service for the app to use
model_manager = ModelManager()
