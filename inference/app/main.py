import grpc
from concurrent import futures
from llama_cpp import Llama
import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
from grpc_reflection.v1alpha import reflection
import os
import logging
import threading
import time
from utils import IS_GPU_AVAILABLE
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODELS_PATH = "/models/"

class ModelStatus(Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    READY = "READY"
    ERROR = "ERROR"

def detect_model_type(model_name, loaded_model=None):
    """
    根据文件名和模型元数据，自动判别模型类型
    """
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
    """Qwen/Yi/部分国产模型需要手动拼prompt"""
    prompt = ""
    for msg in messages:
        if msg['role'] == 'user':
            prompt += "<|im_start|>user\n" + msg['content'] + "<|im_end|>\n"
        elif msg['role'] == 'assistant':
            prompt += "<|im_start|>assistant\n" + msg['content'] + "<|im_end|>\n"
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
        self.model_type = None  # 新增，模型类型
        self.status = ModelStatus.IDLE
        self.error_message = ""
        self.lock = threading.Lock()
        self.initialized = True
        logger.info("模型管理器初始化完成。")

    def _load_model_in_background(self, new_model_name):
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
            # 对部分模型可预传chat_format参数，但不影响大多数类型
            chat_format_to_use = None
            if "qwen" in new_model_name.lower():
                chat_format_to_use = "chatml"
            elif "llama-3" in new_model_name.lower():
                chat_format_to_use = "llama-3"
            elif "llama-2" in new_model_name.lower():
                chat_format_to_use = "llama-2"

            new_model = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_gpu_layers=n_gpu_layers,
                chat_format=chat_format_to_use,
                verbose=True
            )
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

    def switch_model(self, new_model_name):
        with self.lock:
            if self.status == ModelStatus.LOADING:
                return {"status": "loading_busy"}
            if self.model_name == new_model_name and self.status == ModelStatus.READY:
                return {"status": "already_loaded"}
            model_path = os.path.join(MODELS_PATH, new_model_name)
            if not os.path.exists(model_path):
                return {"status": "error", "message": "模型文件不存在"}
            thread = threading.Thread(target=self._load_model_in_background, args=(new_model_name,), name=f"ModelLoader-{new_model_name}")
            thread.daemon = True
            thread.start()
            return {"status": "loading_started", "name": new_model_name}

    def get_model_instance(self):
        if self.status == ModelStatus.READY:
            return self.model
        return None

    def get_model_type(self):
        if self.status == ModelStatus.READY:
            return self.model_type
        return None

    def get_current_status(self):
        return {
            "status": self.status.name,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "error_message": self.error_message
        }

    def infer_stream(self, query, history=None):
        """
        通用推理流，自动适配不同模型类型
        query: 用户输入字符串
        history: 聊天历史 [{"role":"user","content":""},{"role":"assistant","content":""}]
        """
        if self.status != ModelStatus.READY or not self.model:
            raise RuntimeError("模型未就绪")
        messages = []
        if history:
            messages += history
        messages.append({"role": "user", "content": query})

        # Qwen、Yi等需要拼prompt
        if self.model_type in ("qwen", "yi"):
            prompt = build_prompt_qwen(messages)
            for output in self.model.create_completion(prompt=prompt, stream=True):
                token = output["choices"][0].get("text", "")
                if token:
                    yield token
        else:
            for output in self.model.create_chat_completion(messages=messages, stream=True):
                token = output["choices"][0].get("delta", {}).get("content", "")
                if not token:
                    # 兼容部分模型直接用text字段
                    token = output["choices"][0].get("text", "")
                if token:
                    yield token

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    def ListAvailableModels(self, request, context):
        try:
            generation_models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        except FileNotFoundError:
            generation_models = []
        current_generation_model = model_manager.model_name if model_manager.status in [ModelStatus.READY, ModelStatus.LOADING] else ""
        return inference_pb2.ModelListResponse(
            generation_models=generation_models,
            current_generation_model=current_generation_model,
        )

    def SwitchModel(self, request, context):
        result = model_manager.switch_model(request.model_name)
        success = result.get("status") in ("loading_started", "already_loaded")
        message = result.get("message", f"Request to load {request.model_name} accepted.")
        return inference_pb2.SwitchModelResponse(success=success, message=message)

    def ChatStream(self, request, context):
        # 支持后续加多轮历史（如request.history），现在只用query
        try:
            for token in model_manager.infer_stream(query=request.query, history=None):
                yield inference_pb2.ChatResponse(token=token)
        except Exception as e:
            logger.error(f"聊天生成过程中出错: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"[SYSTEM-ERROR] Inference error: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)
    SERVICE_NAMES = (inference_pb2.DESCRIPTOR.services_by_name['InferenceService'].full_name, reflection.SERVICE_NAME)
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("***** gRPC 服务器已成功启动，正在监听端口 50051 *****")

    try:
        available_models = sorted([f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')])
        if available_models:
            model_manager.switch_model(available_models[0])
        else:
            logger.warning(f"在 {MODELS_PATH} 目录下未找到任何 .gguf 模型文件。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在。")

    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
