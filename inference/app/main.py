import grpc
from concurrent import futures
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import app.protos.inference_pb2 as inference_pb2
import app.protos.inference_pb2_grpc as inference_pb2_grpc
from grpc_reflection.v1alpha import reflection
import os, logging, threading, time
from app.utils import IS_GPU_AVAILABLE
from app.config import MAX_TOKENS, EARLY_STOP_TOKENS, USE_KV_CACHE
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s'
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
    if "qwen" in lower: return "qwen"
    elif "yi" in lower: return "yi"
    elif "baichuan" in lower: return "baichuan"
    elif "deepseek" in lower: return "deepseek"
    elif "llama-3" in lower: return "llama-3"
    elif "llama-2" in lower: return "llama-2"
    elif loaded_model and hasattr(loaded_model, "chat_format"):
        cf = getattr(loaded_model, "chat_format")
        if isinstance(cf, str): return cf.lower()
    return "llama"

def build_prompt_qwen(messages):
    prompt = ""
    for msg in messages:
        if msg['role'] == 'user': prompt += "<|im_start|>user\n" + msg['content'] + "<|im_end|>\n"
        elif msg['role'] == 'assistant': prompt += "<|im_start|>assistant\n" + msg['content'] + "<|im_end|>\n"
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
            logger.info(f"加载模型 {new_model_name} 到 {'GPU' if IS_GPU_AVAILABLE else 'CPU'}")
            chat_format = None
            if "qwen" in new_model_name.lower(): chat_format = "chatml"
            elif "llama-3" in new_model_name.lower(): chat_format = "llama-3"
            elif "llama-2" in new_model_name.lower(): chat_format = "llama-2"
            new_model = Llama(model_path=model_path, n_ctx=8192, n_gpu_layers=n_gpu_layers, chat_format=chat_format, verbose=True)
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
            embed_model_path = os.path.join(MODELS_PATH, "embedding-model", "BAAI/bge-base-zh-v1.5")
            if not os.path.isdir(embed_model_path): embed_model_path = "BAAI/bge-base-zh-v1.5"
            device = "cuda" if IS_GPU_AVAILABLE else "cpu"
            self.embedding_model = SentenceTransformer(embed_model_path, device=device)
            self.embedding_model_name = "BAAI/bge-base-zh-v1.5"
            logger.info("加载嵌入模型成功")
        except Exception as e:
            logger.error(f"加载嵌入模型出错: {e}", exc_info=True)

    def switch_model(self, new_model_name):
        with self.lock:
            if self.status == ModelStatus.LOADING:
                return {"status": "loading_busy"}
            if self.model_name == new_model_name and self.status == ModelStatus.READY:
                return {"status": "already_loaded"}
            if not os.path.exists(os.path.join(MODELS_PATH, new_model_name)):
                return {"status": "error", "message": "模型不存在"}
            threading.Thread(target=self._load_model_in_background, args=(new_model_name,), daemon=True).start()
            return {"status": "loading_started", "name": new_model_name}

    def infer_stream(self, query, history=None):
        if self.status != ModelStatus.READY or not self.model:
            raise RuntimeError("模型未就绪")
        messages = history[:] if history else []
        messages.append({"role": "user", "content": query})

        if self.model_type in ("qwen", "yi"):
            prompt = build_prompt_qwen(messages)
            stream = self.model.create_completion(
                prompt=prompt,
                stream=True,
                use_cache=USE_KV_CACHE,
                max_tokens=MAX_TOKENS,
                stop=EARLY_STOP_TOKENS or None,
            )
            for output in stream:
                token = output["choices"][0].get("text", "")
                if token:
                    yield token
        else:
            stream = self.model.create_chat_completion(
                messages=messages,
                stream=True,
                use_cache=USE_KV_CACHE,
                max_tokens=MAX_TOKENS,
                stop=EARLY_STOP_TOKENS or None,
            )
            for output in stream:
                token = output["choices"][0].get("delta", {}).get("content", "")
                if token:
                    yield token


model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    def ListAvailableModels(self, request, context):
        gen, emb = [], []
        try:
            for f in os.listdir(MODELS_PATH):
                if f.endswith('.gguf'):
                    (emb if "embed" in f.lower() else gen).append(f)
        except:
            pass
        embed_dir = os.path.join(MODELS_PATH, "embedding-model")
        if os.path.isdir(embed_dir):
            for sub in os.listdir(embed_dir):
                emb.append(os.path.join("embedding-model", sub))
        current_gen = model_manager.model_name if model_manager.status in (ModelStatus.READY, ModelStatus.LOADING) else ""
        current_emb = model_manager.embedding_model_name or (emb[0] if emb else "")
        device = "GPU" if IS_GPU_AVAILABLE else "CPU"
        return inference_pb2.ModelListResponse(
            generation_models=gen,
            embedding_models=emb,
            current_generation_model=current_gen,
            current_embedding_model=current_emb,
            device=device
        )

    def SwitchModel(self, request, context):
        res = model_manager.switch_model(request.model_name)
        return inference_pb2.SwitchModelResponse(success=res["status"] in ("loading_started", "already_loaded"), message=res.get("message", ""))

    def ChatStream(self, request, context):
        try:
            for token in model_manager.infer_stream(request.query):
                yield inference_pb2.ChatResponse(token=token)
        except Exception as e:
            logger.error(f"Chat 异常: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=str(e))

    def GetEmbeddingsBatch(self, request, context):
        if not model_manager.embedding_model:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return inference_pb2.EmbeddingBatchResponse()
        try:
            vectors = model_manager.embedding_model.encode(request.texts, normalize_embeddings=True)
            return inference_pb2.EmbeddingBatchResponse(embeddings=[inference_pb2.Embedding(values=v.tolist()) for v in vectors])
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.EmbeddingBatchResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)
    reflection.enable_server_reflection((
        inference_pb2.DESCRIPTOR.services_by_name['InferenceService'].full_name,
        reflection.SERVICE_NAME
    ), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC 服务器已启动")
    model_manager._load_embedding_model()
    try:
        available = sorted([f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf') and "embed" not in f.lower()])
        if available: model_manager.switch_model(available[0])
    except:
        logger.error("模型目录不存在")
    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
