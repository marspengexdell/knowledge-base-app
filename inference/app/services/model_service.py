# 文件：inference/app/services/model_service.py

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
        self._scan_models()
        # 自动加载默认生成模型（后台线程）
        if default_model:
            # 异步加载指定默认模型
            self.load_model(default_model, 'generation', async_mode=True)
        elif self.available_models['generation']:
            # 自动加载第一个可用生成模型
            self.load_model(self.available_models['generation'][0], 'generation', async_mode=True)

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
        # 可补充 embedding-model 子目录递归

    def list_models(self):
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
        else:
            _do_load()

    def generate_stream(self, prompt: str, model_name: str = None):
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
            for chunk in model(prompt=prompt, stream=True, max_tokens=512):
                txt = chunk['choices'][0]['text']
                if txt:
                    yield txt
        except Exception as e:
            logging.error(f"推理异常: {e}", exc_info=True)
            yield f"[ERROR] 推理异常: {e}"

    # 切换模型（异步后台加载）
    def switch_model(self, model_name: str, model_type: str = 'generation'):
        self.load_model(model_name, model_type, async_mode=True)
        return True

    def model_status(self):
        with self.lock:
            return {
                "model_loading": self.model_loading,
                "loading_model_name": self.loading_model_name,
                "current_generation_model": self.current_generation_model_name,
                "current_embedding_model": self.current_embedding_model_name,
            }
