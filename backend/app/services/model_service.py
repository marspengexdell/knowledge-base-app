import os
import logging
from threading import Lock, Thread
from llama_cpp import Llama
import time

class RAGService:
    def __init__(self, model_dir: str, default_model: str = None, embed_model_dir: str = None, db_path: str = None):
        self.model_dir = model_dir
        self.embed_model_dir = embed_model_dir
        self.db_path = db_path
        self.lock = Lock()
        self.model_loading = False
        self.loading_model_name = None
        self.current_generation_model = None
        self.current_generation_model_name = ""
        self.current_embedding_model = None
        self.current_embedding_model_name = ""
        self.available_models = {'generation': [], 'embedding': []}
        # 扫描模型目录
        self._scan_models()
        # 自动加载第一个可用的生成模型（后台加载）
        if default_model and default_model in self.available_models['generation']:
            Thread(target=self.load_model, args=(default_model, 'generation', True), daemon=True).start()
        elif self.available_models['generation']:
            first_model = self.available_models['generation'][0]
            Thread(target=self.load_model, args=(first_model, 'generation', True), daemon=True).start()

        # 自动加载第一个嵌入模型
        if self.available_models['embedding']:
            first_embed = self.available_models['embedding'][0]
            Thread(target=self.load_model, args=(first_embed, 'embedding', True), daemon=True).start()

    def _scan_models(self):
        self.available_models = {'generation': [], 'embedding': []}
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        # 扫描根目录下的模型文件
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                lower = filename.lower()
                if 'embed' in lower or 'embedding' in lower:
                    self.available_models['embedding'].append(filename)
                else:
                    self.available_models['generation'].append(filename)
        # 扫描嵌入模型子目录
        embed_dir = os.path.join(self.model_dir, "embedding-model")
        if os.path.isdir(embed_dir):
            for sub in os.listdir(embed_dir):
                if sub.endswith('.gguf') or sub.endswith('.safetensors'):
                    self.available_models['embedding'].append(os.path.join("embedding-model", sub))

    def list_models(self):
        # 返回可用模型列表及当前模型名
        self._scan_models()
        return {
            'generation_models': self.available_models['generation'],
            'embedding_models': self.available_models['embedding'],
            'current_generation_model': self.current_generation_model_name,
            'current_embedding_model': self.current_embedding_model_name,
            'model_loading': self.model_loading,
            'loading_model_name': self.loading_model_name,
        }

    def load_model(self, model_name: str, model_type: str = 'generation', async_mode: bool = False):
        def _do_load():
            with self.lock:
                self.model_loading = True
                self.loading_model_name = model_name
            try:
                model_path = os.path.join(self.model_dir, model_name)
                logging.info(f"开始加载模型：{model_path}")
                t0 = time.time()
                model = Llama(model_path=model_path, n_ctx=2048)
                with self.lock:
                    if model_type == "generation":
                        self.current_generation_model = model
                        self.current_generation_model_name = model_name
                    elif model_type == "embedding":
                        self.current_embedding_model = model
                        self.current_embedding_model_name = model_name
                    logging.info(f"模型 {model_path} 加载完成, 耗时 {time.time() - t0:.2f} 秒")
            except Exception as e:
                logging.error(f"模型加载失败: {e}", exc_info=True)
            finally:
                with self.lock:
                    self.model_loading = False
                    self.loading_model_name = None

        if async_mode:
            Thread(target=_do_load, daemon=True).start()
            return True
        else:
            _do_load()
            return True

    def generate_stream(self, prompt: str, model_name: str = None):
        # 生成流式响应，如果模型正在加载则返回提示
        with self.lock:
            if self.model_loading:
                yield "[ERROR] 模型正在加载中，请稍候"
                return
            model = self.current_generation_model
            current_name = self.current_generation_model_name
        if not model:
            yield "[ERROR] 当前未加载生成模型"
            return
        try:
            # 使用 llama_cpp 模型生成文本
            for chunk in model(prompt=prompt, stream=True, max_tokens=512):
                txt = chunk['choices'][0]['text']
                if txt:
                    yield txt
        except Exception as e:
            logging.error(f"推理异常: {e}", exc_info=True)
            yield f"[ERROR] 推理异常: {e}"

    def generate(self, prompt: str, model_name: str = None) -> str:
        """Convenience wrapper that returns the full generated text."""
        return "".join(self.generate_stream(prompt, model_name))

    def embed(self, text: str):
        """Placeholder embedding method using the current embedding model."""
        if not self.current_embedding_model:
            logging.warning("No embedding model loaded")
            return []
        try:
            # llama_cpp Llama.embed returns a list of floats
            return self.current_embedding_model.embed(text)
        except Exception as e:
            logging.error(f"Embedding failed: {e}", exc_info=True)
            return []

    def switch_model(self, model_name: str, model_type: str = 'generation'):
        # 异步后台加载模型
        return self.load_model(model_name, model_type, async_mode=True)

    def model_status(self):
        with self.lock:
            return {
                "model_loading": self.model_loading,
                "loading_model_name": self.loading_model_name,
                "current_generation_model": self.current_generation_model_name,
                "current_embedding_model": self.current_embedding_model_name,
            }

    def query(self, prompt: str, topk: int = 3):
        # 检索模块暂时未实现，返回空列表
        return []
