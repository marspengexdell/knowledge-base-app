import os
import logging
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGService:
    def __init__(self, model_dir, embed_model_dir, db_path):
        self.model_dir = model_dir
        self.embed_model_dir = embed_model_dir
        self.db_path = db_path

        self.generation_model = None
        self.embedding_model = None

        self.current_generation_model_name = None
        self.current_embedding_model_name = None

        self.generation_models, self.embedding_models = self.list_models()
        self.load_or_die()

    def find_model_path(self, model_name, directory):
        if not model_name:
            return None
        path = os.path.join(directory, model_name)
        if os.path.exists(path):
            return path
        # 兼容相对子目录
        if os.path.exists(model_name):
            return model_name
        return None

    def load_generation_model(self, model_name=None):
        if model_name:
            self.current_generation_model_name = model_name
        if not self.current_generation_model_name:
            logging.error("没有指定生成模型名称。")
            return
        model_path = self.find_model_path(self.current_generation_model_name, self.model_dir)
        if not model_path:
            logging.error(f"生成模型文件不存在: {self.current_generation_model_name}")
            return
        try:
            self.generation_model = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                n_ctx=4096,
                verbose=True
            )
            logging.info(f"成功加载生成模型: {model_path}")
        except Exception as e:
            logging.error(f"加载生成模型失败: {e}")

    def load_embedding_model(self, model_name=None):
        """
        支持 gguf/safetensors 也支持 sentence-transformers 格式（如bge、m3e等）。
        """
        if model_name:
            self.current_embedding_model_name = model_name
        if not self.current_embedding_model_name:
            logging.error("没有指定嵌入模型名称。")
            return

        # 1. sentence-transformers 格式优先（如 models/embedding-model/bge-base-zh/）
        path = os.path.join(self.embed_model_dir, self.current_embedding_model_name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "config.json")):
            try:
                self.embedding_model = SentenceTransformer(path)
                logging.info(f"成功加载 sentence-transformers 嵌入模型: {path}")
                return
            except Exception as e:
                logging.error(f"加载 sentence-transformers 嵌入模型失败: {e}")

        # 2. 如果是 .gguf/.safetensors 格式嵌入模型（极少数情况）
        model_path = self.find_model_path(self.current_embedding_model_name, self.model_dir)
        if model_path and (model_path.endswith(".gguf") or model_path.endswith(".safetensors")):
            try:
                self.embedding_model = Llama(
                    model_path=model_path,
                    embedding=True
                )
                logging.info(f"成功加载 gguf 嵌入模型: {model_path}")
                return
            except Exception as e:
                logging.error(f"加载 gguf 嵌入模型失败: {e}")

        logging.error(f"未能加载任何嵌入模型: {self.current_embedding_model_name}")

    def list_models(self):
        """
        返回生成模型列表、嵌入模型列表（huggingface格式和gguf格式都能识别）
        """
        generation_models = []
        embedding_models = []

        # 生成模型（.gguf/.safetensors）
        if os.path.exists(self.model_dir):
            for filename in os.listdir(self.model_dir):
                if filename.endswith('.gguf') or filename.endswith('.safetensors'):
                    lower = filename.lower()
                    if "embed" in lower or "embedding" in lower:
                        embedding_models.append(filename)
                    else:
                        generation_models.append(filename)
        # 嵌入模型（sentence-transformers 格式文件夹）
        if os.path.exists(self.embed_model_dir):
            for d in os.listdir(self.embed_model_dir):
                sub = os.path.join(self.embed_model_dir, d)
                if os.path.isdir(sub) and os.path.exists(os.path.join(sub, "config.json")):
                    embedding_models.append(d)
        return generation_models, embedding_models

    def load_or_die(self):
        if not self.generation_models:
            raise Exception("No generation model found in /models")
        self.current_generation_model_name = self.generation_models[0]
        self.load_generation_model()
        if self.embedding_models:
            self.current_embedding_model_name = self.embedding_models[0]
            self.load_embedding_model()
        else:
            logging.warning("未找到任何嵌入模型，知识库检索功能将不可用。")

    def generate_stream(self, prompt):
        if not self.generation_model:
            yield "模型未加载，请检查服务端日志。"
            return
        try:
            stream = self.generation_model.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for output in stream:
                token = output["choices"][0]["delta"].get("content")
                if token:
                    yield token
        except Exception as e:
            yield f"文本生成时遇到错误: {e}"

    def embed(self, text):
        """
        对文本做向量化（根据加载模型的类型自动分流）。
        """
        if not self.embedding_model:
            raise Exception("未加载嵌入模型")
        if isinstance(self.embedding_model, SentenceTransformer):
            return self.embedding_model.encode([text])[0]
        elif isinstance(self.embedding_model, Llama):
            # 假如以后用 llama.cpp 做 embedding
            return self.embedding_model.create_embedding(text)
        else:
            raise Exception("未知的嵌入模型类型")
