from sentence_transformers import SentenceTransformer
import threading

class EmbeddingModel:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, model_name_or_path="BAAI/bge-base-zh-v1.5"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.initialized = False
        return cls._instance

    def __init__(self, model_name_or_path="BAAI/bge-base-zh-v1.5"):
        if not getattr(self, "initialized", False):
            self.model_name_or_path = model_name_or_path
            self.model = SentenceTransformer(model_name_or_path)
            self.initialized = True

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True).tolist()

embedding_model = EmbeddingModel()
