import os
from typing import List, Dict, Optional

class ModelService:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.current_generation_model = None
        self.current_generation_model_name = None
        self.current_embedding_model = None
        self.current_embedding_model_name = None
        self._scan_models()

    def _scan_models(self):
        """扫描模型目录，自动区分embedding和generation模型"""
        self.available_models = {'generation': [], 'embedding': []}
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)

    def list_models(self) -> Dict[str, List[str]]:
        self._scan_models()  # 每次调用都刷新
        return self.available_models

    def load_model(self, model_name: str, model_type: Optional[str] = None) -> bool:
        """热切换/按需加载模型。model_type: 'generation' or 'embedding'"""
        model_path = os.path.join(self.model_dir, model_name)
        if not os.path.exists(model_path):
            return False
        if model_type is None:
            lower = model_name.lower()
            model_type = 'embedding' if 'embed' in lower or 'embedding' in lower else 'generation'
        try:
            if model_type == 'generation':
                self.current_generation_model = self._load_local_llm(model_path)
                self.current_generation_model_name = model_name
            elif model_type == 'embedding':
                self.current_embedding_model = self._load_local_embedding(model_path)
                self.current_embedding_model_name = model_name
            else:
                return False
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def _load_local_llm(self, model_path):
        """本地加载生成模型（示例）"""
        # 这里替换成你实际的 LLM 加载代码（如 llama.cpp/transformers）
        return f"[MockGenModel:{model_path}]"

    def _load_local_embedding(self, model_path):
        """本地加载embedding模型（示例）"""
        # 这里替换成 sentence-transformers/llama.cpp embedding 加载
        return f"[MockEmbedModel:{model_path}]"

    def generate(self, prompt: str, model_name: Optional[str] = None) -> str:
        if model_name and model_name != self.current_generation_model_name:
            ok = self.load_model(model_name, model_type='generation')
            if not ok:
                return "[ERROR] 生成模型加载失败"
        if not self.current_generation_model:
            return "[ERROR] 当前未加载生成模型"
        return f"[生成内容:{prompt} 使用模型:{self.current_generation_model_name}]"

    def embed(self, text: str, model_name: Optional[str] = None) -> List[float]:
        if model_name and model_name != self.current_embedding_model_name:
            ok = self.load_model(model_name, model_type='embedding')
            if not ok:
                return []
        if not self.current_embedding_model:
            return []
        return [0.1234, 0.5678]  # mock

    def status(self) -> Dict:
        return {
            'ready': self.current_generation_model is not None,
            'current_generation_model': self.current_generation_model_name,
            'current_embedding_model': self.current_embedding_model_name,
            'msg': 'ok' if self.current_generation_model else '未加载生成模型'
        }
