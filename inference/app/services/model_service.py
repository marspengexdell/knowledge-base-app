import os
from typing import List, Dict, Optional, Union

# llama-cpp-python 必须 import
from llama_cpp import Llama

class ModelService:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.current_generation_model = None  # Llama 对象
        self.current_generation_model_name = ""
        self.current_embedding_model = None  # 可后续扩展
        self.current_embedding_model_name = ""
        self._scan_models()

    def _scan_models(self):
        self.available_models = {'generation': [], 'embedding': []}
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)

    def list_models(self) -> Dict[str, Union[List[str], str]]:
        self._scan_models()
        return {
            'generation_models': self.available_models['generation'],
            'embedding_models': self.available_models['embedding'],
            'current_generation_model': self.current_generation_model_name,
            'current_embedding_model': self.current_embedding_model_name,
        }

    def _modeltype_to_str(self, model_type) -> Optional[str]:
        if isinstance(model_type, int):
            if model_type == 1: return "generation"
            if model_type == 2: return "embedding"
        if isinstance(model_type, str):
            t = model_type.lower()
            if t in ("generation", "gen"): return "generation"
            if t in ("embedding", "embed"): return "embedding"
        return None

    def load_model(self, model_name: str, model_type: Optional[Union[str, int]] = None) -> bool:
        model_path = os.path.join(self.model_dir, model_name)
        if not os.path.exists(model_path):
            print("模型文件不存在", model_path)
            return False
        mtype = self._modeltype_to_str(model_type)
        if not mtype:
            lower = model_name.lower()
            mtype = 'embedding' if 'embed' in lower or 'embedding' in lower else 'generation'
        try:
            if mtype == 'generation':
                # 直接加载 GGUF
                self.current_generation_model = Llama(model_path=model_path, n_ctx=2048)
                self.current_generation_model_name = model_name
            elif mtype == 'embedding':
                # 这里留空，或你自己集成 embedding 模型
                self.current_embedding_model = None
                self.current_embedding_model_name = model_name
            else:
                print("不支持的模型类型", model_type)
                return False
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def generate_stream(self, prompt: str, model_name: Optional[str] = None):
        """
        生成内容流（token流式输出），返回生成 token 的迭代器
        """
        if model_name and model_name != self.current_generation_model_name:
            ok = self.load_model(model_name, model_type='generation')
            if not ok:
                yield "[ERROR] 生成模型加载失败"
                return
        if not self.current_generation_model:
            yield "[ERROR] 当前未加载生成模型"
            return

        # llama.cpp 迭代流式输出
        for chunk in self.current_generation_model(prompt=prompt, stream=True, max_tokens=512, stop=["[DONE]"]):
            # 每个 chunk 是字典，内容在 chunk['choices'][0]['text']
            yield chunk['choices'][0]['text']

    def generate(self, prompt: str, model_name: Optional[str] = None) -> str:
        # 非流式用法，直接返回全部
        return "".join(self.generate_stream(prompt, model_name))

    # ...embed和status等其它函数如前...
