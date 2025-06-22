import grpc
import json
from concurrent import futures
from llama_cpp import Llama
import protos.inference_pb2 as inference_pb2
import protos.inference_pb2_grpc as inference_pb2_grpc
import os
import logging
import threading

# --- 配置 ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_PATH = "/models/"
CONFIG_PATH = "/app/model_config.json" # 我们新创建的配置文件的路径

# --- 全局模型管理器 ---
class ModelManager:
    """一个线程安全的类，用于管理和切换 Llama.cpp 模型实例。"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not hasattr(self, 'initialized'):
            self.model = None
            self.model_name = ""
            self.model_config = self._load_model_config()
            self.lock = threading.Lock() # 用于模型切换操作的锁
            self.initialized = True
            logger.info("模型管理器初始化完成。")

    def _load_model_config(self):
        """加载模型配置文件。"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                logger.info(f"成功加载模型配置文件: {CONFIG_PATH}")
                return config
        except FileNotFoundError:
            logger.error(f"错误：找不到模型配置文件 {CONFIG_PATH}。将使用默认设置。")
            return {"model_chat_formats": {}, "default_chat_format": "llama-2"}
        except json.JSONDecodeError:
            logger.error(f"错误：模型配置文件 {CONFIG_PATH} 格式错误。将使用默认设置。")
            return {"model_chat_formats": {}, "default_chat_format": "llama-2"}

    def _get_chat_format(self, model_path):
        """
        通过临时加载模型元数据来动态确定聊天格式。
        这是一个辅助函数，不应该直接在请求处理中调用。
        """
        try:
            # 为了获取元数据，我们用最少的参数临时加载模型
            temp_llama = Llama(model_path=model_path, n_ctx=512, n_threads=1, verbose=False)
            metadata = temp_llama.metadata
            architecture = metadata.get('general.architecture')
            del temp_llama # 立即释放资源

            if not architecture:
                 logger.warning(f"模型 '{os.path.basename(model_path)}' 的元数据中未找到 'general.architecture'。")
                 return self.model_config['default_chat_format']

            chat_format = self.model_config['model_chat_formats'].get(architecture)

            if chat_format:
                logger.info(f"模型架构 '{architecture}' 匹配成功，将使用聊天模板: '{chat_format}'")
                return chat_format
            else:
                default_format = self.model_config['default_chat_format']
                logger.warning(
                    f"在配置文件中未找到模型架构 '{architecture}' 的聊天模板。 "
                    f"将为 '{os.path.basename(model_path)}' 使用默认模板: '{default_format}'"
                )
                return default_format
        except Exception as e:
            logger.error(f"从元数据获取聊天模板时出错: {e}")
            return self.model_config.get('default_chat_format', 'llama-2')


    def switch_model(self, new_model_name):
        """
        执行模型的热切换。这是一个阻塞操作，并且是线程安全的。
        """
        with self.lock: # 确保同一时间只有一个线程在切换模型
            if self.model_name == new_model_name and self.model is not None:
                logger.info(f"模型 '{new_model_name}' 已经加载。")
                return {"status": "already_loaded", "name": new_model_name}

            model_path = os.path.join(MODELS_PATH, new_model_name)
            if not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return {"status": "error", "message": "模型文件不存在"}

            try:
                # 1. 卸载旧模型
                if self.model is not None:
                    logger.info(f"开始卸载旧模型: {self.model_name}...")
                    # Llama-cpp-python 通过删除实例和垃圾回收来释放内存
                    del self.model
                    self.model = None
                    logger.info("旧模型已卸载。")

                # 2. 动态获取新模型的聊天格式
                logger.info(f"正在为新模型 '{new_model_name}' 确定聊天格式...")
                chat_format = self._get_chat_format(model_path)

                # 3. 加载新模型
                logger.info(f"开始加载新模型: {new_model_name}，使用模板: '{chat_format}'...")
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=8192,
                    n_gpu_layers=-1, # -1 表示尽可能使用所有可用的 GPU 层
                    chat_format=chat_format,
                    verbose=True
                )
                self.model_name = new_model_name
                logger.info(f"成功切换并加载模型: {new_model_name}")
                return {"status": "switched", "name": new_model_name}

            except Exception as e:
                logger.error(f"切换模型时发生严重错误: {e}", exc_info=True)
                self.model = None
                self.model_name = ""
                return {"status": "error", "message": str(e)}

    def get_current_model_info(self):
        """获取当前加载的模型名称。"""
        with self.lock:
            return self.model_name
            
    def get_model(self):
        """获取当前模型实例的引用。"""
        with self.lock:
            return self.model

# 在服务启动时初始化模型管理器
model_manager = ModelManager()

class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    def GetModels(self, request, context):
        """获取模型列表和当前加载的模型。"""
        try:
            models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        except FileNotFoundError:
            logger.error(f"模型目录 {MODELS_PATH} 不存在。")
            models = []
        
        response = inference_pb2.ModelList(
            models=models,
            current_model=model_manager.get_current_model_info()
        )
        return response

    def SwitchModel(self, request, context):
        """处理切换模型的 gRPC 请求。"""
        model_name = request.model_name
        logger.info(f"收到切换模型请求: {model_name}")
        result = model_manager.switch_model(model_name)
        return inference_pb2.SwitchModelResponse(
            status=result.get("status", "error"),
            message=result.get("message", model_name)
        )

    def Chat(self, request_iterator, context):
        """处理聊天流式请求。"""
        model = model_manager.get_model()
        if model is None:
            logger.warning("聊天请求失败，因为没有模型被加载。")
            yield inference_pb2.ChatResponse(reply="[ERROR] No model loaded. Please select a model first.")
            return

        messages = [{"role": request.role, "content": request.content} for request in request_iterator]

        try:
            stream = model.create_chat_completion(messages=messages, stream=True)
            for output in stream:
                if "content" in output["choices"][0]["delta"]:
                    content = output["choices"][0]["delta"]["content"]
                    if content:
                        yield inference_pb2.ChatResponse(reply=content)
        except Exception as e:
            logger.error(f"聊天生成过程中出错: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(reply=f"[ERROR] An error occurred during inference: {e}")

def serve():
    """启动 gRPC 服务器。"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC 服务已在 50051 端口启动...")

    # 自动加载列表中的第一个模型作为默认模型
    try:
        available_models = [f for f in os.listdir(MODELS_PATH) if f.endswith('.gguf')]
        if available_models:
            logger.info(f"找到可用模型: {available_models}。将加载第一个模型作为默认。")
            model_manager.switch_model(available_models[0])
        else:
            logger.warning(f"在 {MODELS_PATH} 目录下未找到任何 .gguf 模型文件。服务将启动但无模型加载。")
    except FileNotFoundError:
        logger.error(f"模型目录 {MODELS_PATH} 不存在，无法自动加载默认模型。")

    server.wait_for_termination()

if __name__ == '__main__':
    serve()