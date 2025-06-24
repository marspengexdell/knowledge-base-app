import grpc
import json
from concurrent import futures
from llama_cpp import Llama
import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
import os
import logging
import threading
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_PATH = "/models/"
CONFIG_PATH = "/app/model_config.json"

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
        self.model_config = self._load_model_config()
        self.lock = threading.Lock()
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

    def switch_model(self, new_model_name):
        with self.lock:
            if self.model_name == new_model_name and self.model is not None:
                logger.info(f"模型 '{new_model_name}' 已是当前加载的模型。")
                return {"status": "already_loaded", "name": new_model_name}

            model_path = os.path.join(MODELS_PATH, new_model_name)
            if not os.path.exists(model_path):
                logger.error(f"请求切换的模型文件不存在: {model_path}")
                return {"status": "error", "message": "模型文件不存在"}

            try:
                if self.model is not None:
                    logger.info(f"开始卸载旧模型: {self.model_name}...")
                    del self.model
                    self.model = None

                logger.info(f"正在为新模型 '{new_model_name}' 确定聊天格式...")
                chat_format = self._get_chat_format(model_path)

                logger.info(f"开始加载新模型: {new_model_name} (模板: '{chat_format}')...")
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_gpu_layers=-1,
                    chat_format=chat_format,
                    verbose=True
                )
                self.model_name = new_model_name
                logger.info(f"***** 成功加载并启用GPU模型: {new_model_name} *****")
                return {"status": "switched", "name": new_model_name}
            except Exception as e:
                logger.error(f"切换模型时发生严重错误: {e}", exc_info=True)
                self.model = None
                self.model_name = ""
                return {"status": "error", "message": str(e)}

    def get_current_model_name(self):
        return self.model_name

    def get_model_instance(self):
        return self.model

model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    def ListAvailableModels(self, request, context):
        try:
            generation_models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        except FileNotFoundError:
            logger.error(f"模型目录 {MODELS_PATH} 不存在。")
            generation_models = []

        current_generation_model = model_manager.get_current_model_name()
        logger.info(
            f"gRPC ListAvailableModels 请求: 返回模型列表 {generation_models}, 当前模型: {current_generation_model}"
        )
        return inference_pb2.ModelListResponse(
            generation_models=generation_models,
            embedding_models=[],
            current_generation_model=current_generation_model,
            current_embedding_model="",
        )

    def SwitchModel(self, request, context):
        model_name = request.model_name
        logger.info(f"gRPC SwitchModel 请求: {model_name}")
        result = model_manager.switch_model(model_name)
        # status 要用 bool success，切记！
        success = result.get("status") in ("switched", "already_loaded")
        message = result.get("message", model_name)
        return inference_pb2.SwitchModelResponse(success=success, message=message)

    # 方法名必须和 proto 一致
    def ChatStream(self, request, context):
        model = model_manager.get_model_instance()
        if model is None:
            logger.warning("ChatStream 请求失败，因为没有模型被加载。")
            yield inference_pb2.ChatResponse(error_message="[SYSTEM-ERROR] No model loaded. Please select a model first.")
            return

        # 只处理单轮 query，后续多轮再升级
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
