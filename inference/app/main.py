import grpc
from concurrent import futures
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer # 【新增】导入嵌入模型库
import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
from grpc_reflection.v1alpha import reflection
import os
import logging
import threading
import time
from utils import IS_GPU_AVAILABLE
from enum import Enum

# ... (日志配置和常量) ...
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
MODELS_PATH = "/models/"

# ... (ModelStatus, detect_model_type, build_prompt_qwen 等辅助函数保持不变) ...
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
        # LLM 相关
        self.model = None
        self.model_name = ""
        self.model_type = None
        self.status = ModelStatus.IDLE
        self.error_message = ""
        # 【新增】Embedding Model 相关
        self.embedding_model = None
        self.embedding_model_name = ""
        # 通用
        self.lock = threading.Lock()
        self.initialized = True
        logger.info("模型管理器初始化完成。")

    # ... (_load_model_in_background 保持不变) ...
    def _load_model_in_background(self, new_model_name):
        # (此函数内容保持不变)
        try:
            with self.lock:
                if self.model is not None:
                    logger.info(f"开始卸载旧模型: {self.model_name}...")
                    del self.model
                    self.model = None
                self.model_name = new_model_name
                self.status = ModelStatus.LOADING
                self.error_message = ""
                self.model_type = None
            model_path = os.path.join(MODELS_PATH, new_model_name)
            n_gpu_layers = -1 if IS_GPU_AVAILABLE else 0
            device = "GPU" if IS_GPU_AVAILABLE else "CPU"
            logger.info(f"将使用 {device} 加载模型: {new_model_name} (n_gpu_layers={n_gpu_layers})")
            chat_format_to_use = None
            if "qwen" in new_model_name.lower(): chat_format_to_use = "chatml"
            elif "llama-3" in new_model_name.lower(): chat_format_to_use = "llama-3"
            elif "llama-2" in new_model_name.lower(): chat_format_to_use = "llama-2"
            new_model = Llama(model_path=model_path, n_ctx=8192, n_gpu_layers=n_gpu_layers, chat_format=chat_format_to_use, verbose=True) # 增加n_ctx
            with self.lock:
                self.model = new_model
                self.model_type = detect_model_type(new_model_name, new_model)
                self.status = ModelStatus.READY
                logger.info(f"***** 成功加载模型: {new_model_name}，类型: {self.model_type} *****")
        except Exception as e:
            logger.error(f"后台切换模型时发生严重错误: {e}", exc_info=True)
            with self.lock:
                self.model = None
                self.model_type = None
                self.status = ModelStatus.ERROR
                self.error_message = str(e)
    
    # 【新增】加载嵌入模型的私有方法
    def _load_embedding_model(self):
        try:
            # 默认加载中文bge模型，或者可以从配置中读取
            embed_model_path = os.path.join(MODELS_PATH, "embedding-model", "BAAI/bge-base-zh-v1.5")
            if not os.path.isdir(embed_model_path):
                 embed_model_path = "BAAI/bge-base-zh-v1.5" # 如果本地没有，从HuggingFace下载
            
            logger.info(f"正在加载嵌入模型: {embed_model_path}...")
            device = "cuda" if IS_GPU_AVAILABLE else "cpu"
            self.embedding_model = SentenceTransformer(embed_model_path, device=device)
            self.embedding_model_name = "BAAI/bge-base-zh-v1.5"
            logger.info("***** 成功加载嵌入模型 *****")
        except Exception as e:
            logger.error(f"加载嵌入模型时发生错误: {e}", exc_info=True)

    # ... (switch_model, get_model_instance, etc. 保持不变) ...
    def switch_model(self, new_model_name):
        with self.lock:
            if self.status == ModelStatus.LOADING: return {"status": "loading_busy"}
            if self.model_name == new_model_name and self.status == ModelStatus.READY: return {"status": "already_loaded"}
            model_path = os.path.join(MODELS_PATH, new_model_name)
            if not os.path.exists(model_path): return {"status": "error", "message": "模型文件不存在"}
            thread = threading.Thread(target=self._load_model_in_background, args=(new_model_name,), name=f"ModelLoader-{new_model_name}")
            thread.daemon = True
            thread.start()
            return {"status": "loading_started", "name": new_model_name}

    def get_model_instance(self):
        if self.status == ModelStatus.READY: return self.model
        return None

    def get_model_type(self):
        if self.status == ModelStatus.READY: return self.model_type
        return None

    def get_current_status(self):
        return {"status": self.status.name, "model_name": self.model_name, "model_type": self.model_type, "error_message": self.error_message}

    def infer_stream(self, query, history=None):
        if self.status != ModelStatus.READY or not self.model: raise RuntimeError("模型未就绪")
        messages = []
        if history: messages += history
        messages.append({"role": "user", "content": query})
        if self.model_type in ("qwen", "yi"):
            prompt = build_prompt_qwen(messages)
            for output in self.model.create_completion(prompt=prompt, stream=True):
                token = output["choices"][0].get("text", "")
                if token: yield token
        else:
            for output in self.model.create_chat_completion(messages=messages, stream=True):
                token = output["choices"][0].get("delta", {}).get("content", "")
                if not token: token = output["choices"][0].get("text", "")
                if token: yield token

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    # ... (ListAvailableModels, SwitchModel, ChatStream 保持不变) ...
    def ListAvailableModels(self, request, context):
        generation_models = []
        embedding_models = []
        try:
            for f in os.listdir(MODELS_PATH):
                path = os.path.join(MODELS_PATH, f)
                if f.endswith('.gguf'):
                    if "embed" in f.lower() or "embedding" in f.lower(): embedding_models.append(f)
                    else: generation_models.append(f)
        except FileNotFoundError:
            logger.warning(f"主模型目录 {MODELS_PATH} 未找到。")
        embed_dir = os.path.join(MODELS_PATH, "embedding-model")
        if os.path.isdir(embed_dir):
            for sub in os.listdir(embed_dir):
                sub_path = os.path.join(embed_dir, sub)
                if os.path.isdir(sub_path): embedding_models.append(os.path.join("embedding-model", sub))
                elif sub.endswith('.gguf') or sub.endswith('.safetensors'): embedding_models.append(os.path.join("embedding-model", sub))
        current_generation_model = model_manager.model_name if model_manager.status in [ModelStatus.READY, ModelStatus.LOADING] else ""
        current_embedding_model = model_manager.embedding_model_name or (embedding_models[0] if embedding_models else "")
        device = "GPU" if IS_GPU_AVAILABLE else "CPU"
        return inference_pb2.ModelListResponse(generation_models=generation_models, embedding_models=embedding_models, current_generation_model=current_generation_model, current_embedding_model=current_embedding_model, device=device)

    def SwitchModel(self, request, context):
        result = model_manager.switch_model(request.model_name)
        success = result.get("status") in ("loading_started", "already_loaded")
        message = result.get("message", f"Request to load {request.model_name} accepted.")
        return inference_pb2.SwitchModelResponse(success=success, message=message)

    def ChatStream(self, request, context):
        try:
            for token in model_manager.infer_stream(query=request.query, history=None):
                yield inference_pb2.ChatResponse(token=token)
        except Exception as e:
            logger.error(f"聊天生成过程中出错: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"[SYSTEM-ERROR] Inference error: {e}")
            
    # 【新增】实现批量嵌入的具体逻辑
    def GetEmbeddingsBatch(self, request, context):
        if not model_manager.embedding_model:
            logger.error("嵌入模型未加载，无法处理批量嵌入请求。")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Embedding model is not ready.")
            return inference_pb2.EmbeddingBatchResponse()
        
        logger.info(f"正在为 {len(request.texts)} 条文本批量生成嵌入...")
        try:
            vectors = model_manager.embedding_model.encode(
                request.texts,
                normalize_embeddings=True
            )
            response_embeddings = []
            for vec in vectors:
                embedding_msg = inference_pb2.Embedding(values=vec.tolist())
                response_embeddings.append(embedding_msg)
            
            return inference_pb2.EmbeddingBatchResponse(embeddings=response_embeddings)
        except Exception as e:
            logger.error(f"批量嵌入时发生错误: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error during batch embedding: {str(e)}")
            return inference_pb2.EmbeddingBatchResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)
    SERVICE_NAMES = (inference_pb2.DESCRIPTOR.services_by_name['InferenceService'].full_name, reflection.SERVICE_NAME)
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("***** gRPC 服务器已成功启动，正在监听端口 50051 *****")

    # 【新增】在启动时就加载嵌入模型
    model_manager._load_embedding_model()

    # 自动加载第一个LLM
    try:
        available_models = sorted([f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf') and "embed" not in f.lower()])
        if available_models:
            model_manager.switch_model(available_models[0])
        else:
            logger.warning(f"在 {MODELS_PATH} 目录下未找到任何 .gguf 生成模型文件。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在。")

    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()