import grpc
from concurrent import futures
import os
import logging
import threading
import time
import json
from enum import Enum

import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
from grpc_reflection.v1alpha import reflection

from config import MAX_TOKENS, EARLY_STOP_TOKENS
from utils import IS_GPU_AVAILABLE

from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
from diskcache import Cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MODELS_PATH = "/models/"

class ModelStatus(Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    READY = "READY"
    ERROR = "ERROR"

def detect_model_type(model_name, loaded_model=None):
    lower = model_name.lower()
    if "qwen" in lower:
        return "qwen"
    elif "yi" in lower:
        return "yi"
    elif "baichuan" in lower:
        return "baichuan"
    elif "deepseek" in lower:
        return "deepseek"
    elif "llama-3" in lower:
        return "llama-3"
    elif "llama-2" in lower:
        return "llama-2"
    elif loaded_model and hasattr(loaded_model, "chat_format"):
        cf = getattr(loaded_model, "chat_format")
        if isinstance(cf, str):
            return cf.lower()
    return "llama"

def build_prompt_qwen(messages):
    prompt = ""
    for msg in messages:
        if msg["role"] == "user":
            prompt += f"<|im_start|>user\n{msg['content']}<|im_end|>\n"
        elif msg["role"] == "assistant":
            prompt += f"<|im_start|>assistant\n{msg['content']}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt

class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.model = None
        self.model_name = ""
        self.model_type = None
        self.status = ModelStatus.IDLE
        self.error_message = ""
        self.embedding_model = None
        self.embedding_model_name = ""
        self.lock = threading.Lock()
        self.cache = Cache("/app/.cache")
        self.initialized = True
        logger.info("模型管理器初始化完成。")

    def _load_model_in_background(self, new_model_name):
        try:
            with self.lock:
                if self.model is not None:
                    del self.model
                self.model_name = new_model_name
                self.status = ModelStatus.LOADING
                self.error_message = ""
                self.model_type = None

            model_path = os.path.join(MODELS_PATH, new_model_name)
            n_gpu_layers = -1 if IS_GPU_AVAILABLE else 0
            logger.info(
                f"加载模型 {new_model_name} 到 {'GPU' if IS_GPU_AVAILABLE else 'CPU'}"
            )

            chat_format = None
            if "qwen" in new_model_name.lower():
                chat_format = "chatml"
            elif "llama-3" in new_model_name.lower():
                chat_format = "llama-3"
            elif "llama-2" in new_model_name.lower():
                chat_format = "llama-2"

            new_model = Llama(
                model_path=model_path,
                n_ctx=8192,
                n_gpu_layers=n_gpu_layers,
                chat_format=chat_format,
                verbose=True,
            )

            with self.lock:
                self.model = new_model
                self.model_type = detect_model_type(new_model_name, new_model)
                self.status = ModelStatus.READY
                logger.info(f"成功加载模型 {new_model_name}")
        except Exception as e:
            logger.error(f"加载模型出错: {e}", exc_info=True)
            with self.lock:
                self.model = None
                self.model_type = None
                self.status = ModelStatus.ERROR
                self.error_message = str(e)

    def _load_embedding_model(self):
        try:
            embedding_root = os.path.join(MODELS_PATH, "embedding-model")
            embed_model_path = None
            if os.path.isdir(embedding_root):
                candidates = [os.path.join(embedding_root, d)
                              for d in os.listdir(embedding_root)
                              if os.path.isdir(os.path.join(embedding_root, d))]
                if candidates:
                    embed_model_path = candidates[0]
                    logger.info(f"发现并加载本地嵌入模型: {embed_model_path}")
                else:
                    logger.warning(f"{embedding_root} 下未发现子目录，将回退到 HuggingFace 下载。")
            if not embed_model_path:
                embed_model_path = "BAAI/bge-base-zh-v1.5"
                logger.info(f"使用 HuggingFace 下载模型: {embed_model_path}")

            device = "cuda" if IS_GPU_AVAILABLE else "cpu"
            self.embedding_model = SentenceTransformer(embed_model_path, device=device)
            self.embedding_model_name = os.path.basename(embed_model_path)
            logger.info(f"嵌入模型加载成功: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"加载嵌入模型出错: {e}", exc_info=True)

    def switch_embedding_model(self, embed_model_path: str):
        """Load a specific embedding model from the given path or HF repo."""
        with self.lock:
            if (
                self.embedding_model is not None
                and os.path.basename(embed_model_path) == self.embedding_model_name
            ):
                return {"status": "already_loaded"}
        try:
            device = "cuda" if IS_GPU_AVAILABLE else "cpu"
            embedding_model = SentenceTransformer(embed_model_path, device=device)
            with self.lock:
                self.embedding_model = embedding_model
                self.embedding_model_name = os.path.basename(embed_model_path)
            logger.info(f"嵌入模型加载成功: {self.embedding_model_name}")
            return {"status": "loaded"}
        except Exception as e:
            logger.error(f"加载嵌入模型出错: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def switch_model(self, new_model_name):
        with self.lock:
            if self.status == ModelStatus.LOADING:
                return {"status": "loading_busy"}
            if self.model_name == new_model_name and self.status == ModelStatus.READY:
                return {"status": "already_loaded"}
            if not os.path.exists(os.path.join(MODELS_PATH, new_model_name)):
                return {"status": "error", "message": "模型不存在"}

            threading.Thread(
                target=self._load_model_in_background,
                args=(new_model_name,),
                daemon=True,
            ).start()
            return {"status": "loading_started", "name": new_model_name}

    def compress_history(
        self, messages: list, max_length: int = 4096, keep_last: int = 4
    ) -> list:
        total_len = sum(len(msg["content"]) for msg in messages)

        if total_len <= max_length:
            return messages

        logger.info("Context length exceeded, compressing history...")
        to_summarize = messages[:-keep_last]

        summary_prompt = (
            "请用一段话精简地总结以下对话的核心内容，以便我能理解后续对话的背景:\n"
        )
        for msg in to_summarize:
            summary_prompt += f"{msg['role']}: {msg['content']}\n"

        response = self.model.create_chat_completion(
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2,
            max_tokens=256,
        )
        summary_text = response["choices"][0]["message"]["content"]

        new_history = [{"role": "system", "content": f"先前对话摘要: {summary_text}"}]
        new_history.extend(messages[-keep_last:])

        logger.info(f"History compressed. New length: {len(new_history)} messages.")
        return new_history

    def infer_stream(self, messages: list):
        if self.status != ModelStatus.READY or not self.model:
            raise RuntimeError("模型未就绪")

        compressed_messages = self.compress_history(messages)
        cache_key = json.dumps(compressed_messages, sort_keys=True)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            yield cached_result
            return

        stream = self.model.create_chat_completion(
            messages=compressed_messages,
            stream=True,
            max_tokens=MAX_TOKENS,
            stop=EARLY_STOP_TOKENS or None,
        )
        full_response = ""
        for output in stream:
            token = output["choices"][0].get("delta", {}).get("content", "")
            if token:
                full_response += token
                yield token

        self.cache[cache_key] = full_response

    def get_embeddings_batch(self, texts):
        if not self.embedding_model:
            raise RuntimeError("嵌入模型未加载")
        vectors = self.embedding_model.encode(texts, normalize_embeddings=True)
        return vectors

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    def ListAvailableModels(self, request, context):
        gen_models = []
        try:
            if os.path.isdir(MODELS_PATH):
                for f in os.listdir(MODELS_PATH):
                    if f.endswith(".gguf"):
                        gen_models.append(f)
        except FileNotFoundError:
            logger.warning(f"模型目录 {MODELS_PATH} 未找到。")

        current_gen = (
            model_manager.model_name
            if model_manager.status in (ModelStatus.READY, ModelStatus.LOADING)
            else ""
        )
        device = "GPU" if IS_GPU_AVAILABLE else "CPU"

        return inference_pb2.ModelListResponse(
            generation_models=gen_models,
            embedding_models=[model_manager.embedding_model_name],
            current_generation_model=current_gen,
            current_embedding_model=model_manager.embedding_model_name,
            device=device,
        )

    def SwitchModel(self, request, context):
        if request.model_type == inference_pb2.ModelType.EMBEDDING:
            res = model_manager.switch_embedding_model(request.model_name)
            success = res["status"] in ("loaded", "already_loaded")
        else:
            res = model_manager.switch_model(request.model_name)
            success = res["status"] in ("loading_started", "already_loaded")
        msg = res.get("message", "") or res.get("status", "")
        return inference_pb2.SwitchModelResponse(success=success, message=msg)

    def ChatStream(self, request, context):
        """
        流式对话接口实现
        """
        try:
            messages = [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ]
            for token in model_manager.infer_stream(messages):
                yield inference_pb2.ChatResponse(token=token)
        except Exception as e:
            logger.error(f"ChatStream 异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            yield inference_pb2.ChatResponse(error_message=str(e))

    def GetEmbeddingsBatch(self, request, context):
        """
        批量获取文本embedding
        """
        if not model_manager.embedding_model:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("嵌入模型未加载。")
            return inference_pb2.EmbeddingBatchResponse()
        try:
            texts = list(request.texts)
            vectors = model_manager.get_embeddings_batch(texts)
            # 注意proto结构！！如果你的proto不是values, 请调整
            return inference_pb2.EmbeddingBatchResponse(
                embeddings=[
                    inference_pb2.Embedding(values=list(map(float, v)))
                    for v in vectors
                ]
            )
        except Exception as e:
            logger.error(f"生成嵌入向量时出错: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"生成嵌入向量时出错: {e}")
            return inference_pb2.EmbeddingBatchResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceService(), server
    )

    SERVICE_NAMES = (
        inference_pb2.DESCRIPTOR.services_by_name["InferenceService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port("[::]:50051")
    server.start()
    logger.info("gRPC 服务器已启动，监听端口 50051")

    # 启动时加载嵌入模型和默认的生成模型
    threading.Thread(target=model_manager._load_embedding_model, daemon=True).start()
    try:
        if os.path.isdir(MODELS_PATH):
            available = sorted(
                [
                    f
                    for f in os.listdir(MODELS_PATH)
                    if f.endswith(".gguf")
                ]
            )
            if available:
                logger.info(f"找到默认模型，正在加载: {available[0]}")
                model_manager.switch_model(available[0])
            else:
                logger.warning(f"模型目录 {MODELS_PATH} 中没有找到 .gguf 模型文件。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在，无法加载默认模型。")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("收到关闭信号，正在停止服务器...")
        server.stop(0)

if __name__ == "__main__":
    serve()
