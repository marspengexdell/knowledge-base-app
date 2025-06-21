import os
from llama_cpp import Llama

class ModelService:
    def __init__(self):
        self.model_dir = "/app/models"  # 必须和docker一致
        self.current_generation_model = None
        self.current_generation_model_name = ""
        self.current_embedding_model = None
        self.current_embedding_model_name = ""
        self._scan_models()

    def _scan_models(self):
        self.available_models = {"generation": [], "embedding": []}
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)
        # 递归embedding-model子目录
        embedding_subdir = os.path.join(self.model_dir, "embedding-model")
        if os.path.isdir(embedding_subdir):
            for subdir in os.listdir(embedding_subdir):
                self.available_models['embedding'].append(os.path.join("embedding-model", subdir))

    def load_generation_model(self, model_name):
        path = os.path.join(self.model_dir, model_name)
        self.current_generation_model = Llama(model_path=path, n_ctx=2048)
        self.current_generation_model_name = model_name

    def load_embedding_model(self, embedding_model_dir):
        # 这里视你实际embedding模型加载方式而定
        path = os.path.join(self.model_dir, embedding_model_dir)
        # 加载embedding逻辑...
        self.current_embedding_model_name = embedding_model_dir

    # 其他相关函数...
