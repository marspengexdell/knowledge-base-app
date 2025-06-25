import os
from llama_cpp import Llama

class ModelService:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.current_generation_model = None
        self.current_generation_model_name = ""
        self.current_embedding_model = None
        self.current_embedding_model_name = ""
        self.available_models = {'generation': [], 'embedding': []}
        self._scan_models()
        # 自动加载默认生成和嵌入模型
        if self.available_models['generation']:
            self.load_generation_model(self.available_models['generation'][0])
        if self.available_models['embedding']:
            self.load_embedding_model(self.available_models['embedding'][0])

    def _scan_models(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)

    def load_generation_model(self, model_name):
        model_path = os.path.join(self.model_dir, model_name)
        self.current_generation_model = Llama(model_path=model_path)
        self.current_generation_model_name = model_name

    def load_embedding_model(self, model_name):
        model_path = os.path.join(self.model_dir, model_name)
        self.current_embedding_model = Llama(model_path=model_path, embedding=True)
        self.current_embedding_model_name = model_name

    # 你还可以加接口暴露用于API切换/加载新嵌入模型
