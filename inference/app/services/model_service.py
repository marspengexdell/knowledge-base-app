import os
import logging
from typing import List, Dict, Optional, Union
from threading import Lock
from llama_cpp import Llama

class RAGService:
    def __init__(self, model_dir: str, embed_model_dir: str = None, db_path: str = None):
        self.model_dir = model_dir
        self.embed_model_dir = embed_model_dir
        self.db_path = db_path
        self.current_generation_model = None
        self.current_generation_model_name = ""
        self.current_embedding_model = None
        self.current_embedding_model_name = ""
        self._scan_models()
        self._load_lock = Lock()

    def _scan_models(self):
        self.available_models = {'generation': [], 'embedding': []}
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)
        # 递归 embedding-model 子目录
        embedding_subdir = os.path.join(self.model_dir, "embedding-model")
        if os.path.isdir(embedding_subdir):
            for subdir in os.listdir(embedding_subdir):
                self.available_models['embedding'].append(os.path.join("embedding-model", subdir))

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
            logging.error(f"模型文件不存在: {model_path}")
            return False
        mtype = self._modeltype_to_str(model_type)
        if not mtype:
            lower = model_name.lower()
            mtype = 'embedding' if 'embed' in lower or 'embedding' in lower else 'generation'
        try:
            with self._load_lock:  # 保证切换线程安全
                if mtype == 'generation':
                    if self.current_generation_model is not None:
                        try:
                            del self.current_generation_model
                        except Exception as e:
                            logging.warning(f"释放旧模型失败: {e}")
                    self.current_generation_model = Llama(model_path=model_path, n_ctx=2048)
                    self.current_generation_model_name = model_name
                    logging.info(f"已加载生成模型: {model_name}")
                elif mtype == 'embedding':
                    # TODO: 这里扩展 embedding 模型加载
                    self.current_embedding_model = None
                    self.current_embedding_model_name = model_name
                    logging.info(f"已加载嵌入模型: {model_name}")
                else:
                    logging.error(f"不支持的模型类型: {model_type}")
                    return False
            return True
        except Exception as e:
            logging.error(f"模型加载失败: {e}", exc_info=True)
            return False

    def generate_stream(self, prompt: str, model_name: Optional[str] = None):
        if model_name and model_name != self.current_generation_model_name:
            ok = self.load_model(model_name, model_type='generation')
            if not ok:
                yield "[ERROR] 生成模型加载失败"
                return
        if not self.current_generation_model:
            yield "[ERROR] 当前未加载生成模型"
            return
        try:
            any_output = False
            for chunk in self.current_generation_model(
                prompt=prompt, stream=True, max_tokens=512, stop=["[DONE]"]
            ):
                txt = chunk['choices'][0]['text']
                if txt is not None:
                    any_output = True
                    yield txt
            if not any_output:
                yield "[ERROR] 推理无内容"
        except Exception as e:
            logging.error(f"推理时发生异常: {e}", exc_info=True)
            yield f"[ERROR] 推理异常: {e}"

    def generate(self, prompt: str, model_name: Optional[str] = None) -> str:
        return "".join(self.generate_stream(prompt, model_name))

    # 补充：假如你后续要写RAG检索，可以在这里实现
    def query(self, query, topk=3):
        # TODO: 这里写你自己的RAG向量检索逻辑
        return []
