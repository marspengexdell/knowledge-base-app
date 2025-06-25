import grpc
import json
from concurrent import futures
from llama_cpp import Llama
import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
from grpc_reflection.v1alpha import reflection
import os
import logging
import threading
import time
from enum import Enum

# --- 核心修改 1: 使用更清晰的日志格式 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODELS_PATH = "/models/"
CONFIG_PATH = "/app/model_config.json"

# --- 核心修改 2: 定义模型状态枚举 ---
class ModelStatus(Enum):
    IDLE = "IDLE"           # 空闲，无模型
    LOADING = "LOADING"     # 正在加载中
    READY = "READY"         # 模型已就绪，可供使用
    ERROR = "ERROR"         # 加载时发生错误

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
        self.status = ModelStatus.IDLE
        self.error_message = ""
        self.model_config = self._load_model_config()
        self.lock = threading.Lock()  # 这个锁用于保护模型实例的访问和修改
        self.initialized = True
        logger.info("模型管理器初始化完成。")

    def _load_model_config(self):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                logger.info(f"成功加载模型配置文件: {CONFIG_PATH}")
                return config
        except Exception as e:
            logger.error(f"无法加载或解析模型配置文件 {CONFIG_PATH}: {e}。将使用默认设置。")
            return {"model_chat_formats": {"llama": "llama-2"}, "default_chat_format": "llama-2"}

    def _get_chat_format(self, model_path):
        try:
            # 这里的临时加载是为了速度，所以不使用GPU
            temp_llama = Llama(model_path=model_path, n_ctx=512, n_gpu_layers=0, verbose=False)
            metadata = temp_llama.metadata
            architecture = metadata.get('general.architecture')
            del temp_llama

            if not architecture:
                logger.warning(f"模型 '{os.path.basename(model_path)}' 元数据中未找到架构信息。")
                return self.model_config['default_chat_format']

            chat_format = self.model_config['model_chat_formats'].get(architecture)
            if chat_format:
                logger.info(f"模型架构 '{architecture}' 匹配成功, 使用聊天模板: '{chat_format}'")
                return chat_format
            else:
                default_format = self.model_config['default_chat_format']
                logger.warning(f"未在配置中找到架构 '{architecture}' 的模板, 将使用默认模板: '{default_format}'")
                return default_format
        except Exception as e:
            logger.error(f"从元数据获取聊天模板时出错: {e}", exc_info=True)
            return self.model_config.get('default_chat_format', 'llama-2')

    # --- 核心修改 3: 实际加载模型的后台方法 ---
    def _load_model_in_background(self, new_model_name):
        try:
            with self.lock:
                # 释放旧模型
                if self.model is not None:
                    logger.info(f"开始卸载旧模型: {self.model_name}...")
                    del self.model
                    self.model = None
                
                # 更新状态
                self.model_name = new_model_name
                self.status = ModelStatus.LOADING
                self.error_message = ""

            logger.info(f"正在后台为新模型 '{new_model_name}' 确定聊天格式...")
            model_path = os.path.join(MODELS_PATH, new_model_name)
            chat_format = self._get_chat_format(model_path)

            logger.info(f"开始在后台加载新模型: {new_model_name} (模板: '{chat_format}')...")
            logger.info("这是一个耗时操作，可能需要几分钟。请观察下方来自 llama.cpp 的详细日志。")
            
            new_model = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_gpu_layers=-1,
                chat_format=chat_format,
                verbose=True
            )

            with self.lock:
                self.model = new_model
                self.status = ModelStatus.READY
                logger.info(f"***** 成功加载并启用GPU模型: {new_model_name} *****")
                logger.info("请在日志中回溯查找 'offloaded ... layers to GPU' 和 'CUDA' 相关字样，以确认GPU加速已启用。")

        except Exception as e:
            logger.error(f"后台切换模型时发生严重错误: {e}", exc_info=True)
            with self.lock:
                self.model = None
                # self.model_name 保持为目标模型，以便前端知道是哪个模型加载失败
                self.status = ModelStatus.ERROR
                self.error_message = str(e)
    
    # --- 核心修改 4: 切换模型的非阻塞方法 ---
    def switch_model(self, new_model_name):
        with self.lock:
            # 如果正在加载中，则不允许切换
            if self.status == ModelStatus.LOADING:
                logger.warning(f"请求切换到 '{new_model_name}'，但当前正在加载 '{self.model_name}'。请稍后重试。")
                return {"status": "loading_busy", "message": f"Cannot switch, currently loading {self.model_name}"}

            # 如果请求的模型已就绪
            if self.model_name == new_model_name and self.status == ModelStatus.READY:
                logger.info(f"模型 '{new_model_name}' 已是当前加载的模型。")
                return {"status": "already_loaded", "name": new_model_name}

            model_path = os.path.join(MODELS_PATH, new_model_name)
            if not os.path.exists(model_path):
                logger.error(f"请求切换的模型文件不存在: {model_path}")
                return {"status": "error", "message": "模型文件不存在"}

            # 启动后台加载线程
            thread = threading.Thread(target=self._load_model_in_background, args=(new_model_name,), name=f"ModelLoader-{new_model_name}")
            thread.daemon = True
            thread.start()
            logger.info(f"已启动后台线程来加载模型 '{new_model_name}'。")

            return {"status": "loading_started", "name": new_model_name}

    def get_current_status(self):
        with self.lock:
            device = "cuda" if os.path.exists("/dev/nvidia0") else "cpu"
            return {
                "model_name": self.model_name,
                "status": self.status.value,
                "error_message": self.error_message,
                "device": device,
            }

    def get_model_instance(self):
        # 仅在模型就绪时返回实例
        if self.status == ModelStatus.READY:
            return self.model
        return None

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):

    # --- 核心修改 5: 新增状态查询 gRPC 接口的实现 ---
    def GetModelStatus(self, request, context):
        status_info = model_manager.get_current_status()
        return inference_pb2.ModelStatusResponse(
            model_name=status_info["model_name"],
            status=status_info["status"],
            error_message=status_info["error_message"]
        )

    def ListAvailableModels(self, request, context):
        try:
            generation_models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        except FileNotFoundError:
            logger.error(f"模型目录 {MODELS_PATH} 不存在。")
            generation_models = []

        status_info = model_manager.get_current_status()
        current_generation_model = status_info["model_name"] if status_info["status"] in ["READY", "LOADING"] else ""
        
        logger.debug(
            f"gRPC ListAvailableModels 请求: 返回模型列表 {generation_models}, 当前模型: {current_generation_model}"
        )
        return inference_pb2.ModelListResponse(
            generation_models=generation_models,
            embedding_models=[],
            current_generation_model=current_generation_model,
            current_embedding_model="",
            device=status_info.get("device", ""),
        )

    def SwitchModel(self, request, context):
        model_name = request.model_name
        logger.info(f"gRPC SwitchModel 请求: {model_name}")
        result = model_manager.switch_model(model_name)
        
        success = result.get("status") in ("loading_started", "already_loaded")
        message = result.get("message", f"Request to load {model_name} accepted.")
        
        return inference_pb2.SwitchModelResponse(success=success, message=message)

    def ChatStream(self, request, context):
        model = model_manager.get_model_instance()
        if model is None:
            status_info = model_manager.get_current_status()
            logger.warning(f"ChatStream 请求失败，模型状态为: {status_info['status']}")
            
            error_msg = f"[SYSTEM-ERROR] Model is not ready. Current status: {status_info['status']}."
            if status_info['status'] == 'ERROR':
                error_msg += f" Details: {status_info['error_message']}"
            elif status_info['status'] == 'LOADING':
                 error_msg += f" Model '{status_info['model_name']}' is currently being loaded."

            yield inference_pb2.ChatResponse(error_message=error_msg)
            return

        messages = [{"role": "user", "content": request.query}]
        try:
            stream = model.create_chat_completion(messages=messages, stream=True)
            for output in stream:
                content = output["choices"][0]["delta"].get("content")
                if content:
                    yield inference_pb2.ChatResponse(token=content)
        except Exception as e:
            logger.error(f"聊天生成过程中出错: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"[SYSTEM-ERROR] An error occurred during inference: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)

    SERVICE_NAMES = (
        inference_pb2.DESCRIPTOR.services_by_name['InferenceService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("***** gRPC 服务器已成功启动，正在监听端口 50051 *****")

    try:
        available_models = sorted([f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')])
        if available_models:
            logger.info(f"找到可用模型: {available_models}。将加载第一个作为默认模型。")
            model_manager.switch_model(available_models[0])
        else:
            logger.warning(f"在 {MODELS_PATH} 目录下未找到任何 .gguf 模型文件。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在，无法自动加载默认模型。")

    logger.info("--- 服务已就绪，等待请求 ---")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("服务关闭。")
        server.stop(0)

if __name__ == '__main__':
    serve()
