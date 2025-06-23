import grpc
from concurrent import futures
import logging
import sys
import os
from protos import inference_pb2, inference_pb2_grpc

# 将 services 包的路径添加到 sys.path
# 这能确保无论在何种环境下都能正确导入 RAGService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.model_service import RAGService

# --- 配置 ---
MODEL_DIR = "/models"
EMBED_MODEL_DIR = "/models/embedding-model" # 保留供未来使用
RAG_DB_PATH = "/app/vector_db.pkl"        # 保留供未来使用

# 配置基本日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量
model_service = None

class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def ChatStream(self, request, context):
        if model_service is None or model_service.generation_model is None:
            logging.error("ChatStream 请求失败，因为模型服务未初始化或模型加载失败。")
            yield inference_pb2.ChatResponse(error_message="服务端模型未就绪，请查看服务端日志。")
            return

        prompt = request.query
        logging.info(f"[PROMPT] {prompt}")
        try:
            # ... (这部分逻辑和之前一样)
            for token in model_service.generate_stream(prompt):
                yield inference_pb2.ChatResponse(token=token)
            yield inference_pb2.ChatResponse(token="[DONE]")
        except Exception as e:
            logging.error(f"ChatStream error: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"服务端异常: {e}")
    
    # ... ListAvailableModels 和 SwitchModel 方法可以保持不变 ...

def serve():
    global model_service
    
    logging.info("--- gRPC 服务启动流程开始 ---")
    
    # 关键步骤：用 try-except 包裹初始化过程
    try:
        logging.info("正在初始化 RAGService...")
        # 只有在这一步，我们才真正实例化服务
        model_service = RAGService(model_dir=MODEL_DIR, embed_model_dir=EMBED_MODEL_DIR, db_path=RAG_DB_PATH)
        
        # 检查模型是否加载成功
        if model_service.generation_model is None:
            logging.error("严重错误: RAGService 初始化完成，但生成模型未能加载。请检查模型文件和配置。服务将退出。")
            # 如果没有模型，服务启动就没意义了，直接退出
            sys.exit(1)

    except Exception as e:
        logging.critical(f"在服务初始化阶段发生致命错误，无法启动: {e}", exc_info=True)
        # 发生任何未捕获的异常，都将导致服务启动失败
        sys.exit(1)

    # 如果初始化成功，则启动 gRPC 服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    
    logging.info("***** gRPC 服务器已成功启动，正在监听端口 50051 *****")
    server.start()
    server.wait_for_termination()
    logging.info("--- gRPC 服务已停止 ---")


if __name__ == '__main__':
    serve()