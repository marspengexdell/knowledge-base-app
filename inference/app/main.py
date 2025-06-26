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
import sys  # 用于 flush 输出

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 调试函数 ---
def print_debug(message):
    """一个带高亮标记的打印函数，确保日志能被看到"""
    print(f"\n\n--- [INFERENCE DEBUG] --- {message}\n", flush=True)

MODELS_PATH = "/models/"

class ModelStatus(Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    READY = "READY"
    ERROR = "ERROR"

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
        if self.initialized: return
        self.model = None
        self.model_name = ""
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

            model_path = os.path.join(MODELS_PATH, new_model_name)
            print_debug(f"STEP 1: 开始加载模型文件: {model_path}")
            n_gpu_layers = -1 if IS_GPU_AVAILABLE else 0

            new_model = Llama(
                model_path=model_path, n_ctx=4096, n_gpu_layers=n_gpu_layers, verbose=True
            )

            with self.lock:
                self.model = new_model
                self.status = ModelStatus.READY
                detected_format = getattr(new_model, 'chat_format', '未知')
                # ★ 核心调试点 ★
                print_debug(f"STEP 2: 模型加载完毕。自动检测到的聊天模板格式为: {detected_format}")

                # 打印模型元数据（用于彻底定位 Qwen/Llama 判别）
                print_debug(f"STEP 2+: 模型元数据: {getattr(new_model, 'metadata', None)}")
        except Exception as e:
            print_debug(f"STEP 2 FAILED: 模型加载失败: {e}")
            logger.error(f"后台切换模型时发生严重错误: {e}", exc_info=True)
            with self.lock:
                self.model = None
                self.status = ModelStatus.ERROR
                self.error_message = str(e)

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

    def get_current_status(self):
        with self.lock:
            return {
                "model_name": self.model_name,
                "status": self.status.value,
                "error_message": self.error_message,
                "device": "GPU" if IS_GPU_AVAILABLE else "CPU"
            }

    def get_model_instance(self):
        if self.status == ModelStatus.READY: return self.model
        return None

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):

    def ListAvailableModels(self, request, context):
        try:
            generation_models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        except FileNotFoundError:
            generation_models = []
        status_info = model_manager.get_current_status()
        current_generation_model = status_info["model_name"] if status_info["status"] in ["READY", "LOADING"] else ""
        return inference_pb2.ModelListResponse(
            generation_models=generation_models, embedding_models=[],
            current_generation_model=current_generation_model, current_embedding_model="",
            device=model_manager.get_current_status().get("device", ""),
        )
    def SwitchModel(self, request, context):
        result = model_manager.switch_model(request.model_name)
        success = result.get("status") in ("loading_started", "already_loaded")
        message = result.get("message", f"Request to load {request.model_name} accepted.")
        return inference_pb2.SwitchModelResponse(success=success, message=message)

    def ChatStream(self, request, context):
        print_debug(f"STEP 3: ChatStream 收到请求，用户输入: '{request.query}'")
        model = model_manager.get_model_instance()
        if model is None:
            print_debug("STEP 4 FAILED: 模型未就绪。")
            yield inference_pb2.ChatResponse(error_message="[SYSTEM-ERROR] Model is not ready.")
            return

        messages = [{"role": "user", "content": request.query}]
        print_debug(f"STEP 4: 准备调用模型，传入的消息体: {messages}")

        try:
            stream = model.create_chat_completion(messages=messages, stream=True)
            for i, output in enumerate(stream):
                # ★ 核心调试点 ★
                if i == 0:  # 只打印第一个数据块，避免刷屏
                    print_debug(f"STEP 5: 模型返回的第一个原始数据块: {output}")

                # 兼容所有主流llama-cpp-python返回结构
                content = output["choices"][0].get("delta", {}).get("content", None)
                if content is None:
                    content = output["choices"][0].get("text", "")
                if content:
                    yield inference_pb2.ChatResponse(token=content)
            print_debug("STEP 6: 模型数据流结束。")
        except Exception as e:
            print_debug(f"STEP 5 FAILED: 调用模型时出错: {e}")
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
        if available_models: model_manager.switch_model(available_models[0])
        else: logger.warning(f"在 {MODELS_PATH} 目录下未找到任何 .gguf 模型文件。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在，无法自动加载默认模型。")
    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt: server.stop(0)
if __name__ == '__main__': serve()
