import grpc
from concurrent import futures
import logging
import sys
import os # <--- 我已经在这里加上了这行缺失的导入

from protos import inference_pb2, inference_pb2_grpc
from services.model_service import RAGService

# --- 配置 ---
MODEL_DIR = "/models"
EMBED_MODEL_DIR = "/models/embedding-model"
RAG_DB_PATH = "/app/vector_db.pkl"

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
            for token in model_service.generate_stream(prompt):
                yield inference_pb2.ChatResponse(token=token)
            yield inference_pb2.ChatResponse(token="[DONE]")
        except Exception as e:
            logging.error(f"ChatStream error: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"服务端异常: {e}")

    def ListAvailableModels(self, request, context):
        # 这个方法保持不变
        try:
            models_info = model_service.list_models_info() # 假设 model_service 有这个方法
            return inference_pb2.ModelListResponse(
                generation_models=models_info.get("generation_models", []),
                embedding_models=models_info.get("embedding_models", []),
                current_generation_model=models_info.get("current_generation_model", ""),
                current_embedding_model=models_info.get("current_embedding_model", "")
            )
        except Exception as e:
            logging.error(f"ListAvailableModels error: {e}", exc_info=True)
            return inference_pb2.ModelListResponse()

    def SwitchModel(self, request, context):
        # 这个方法也保持不变
        try:
            model_name = request.model_name
            model_type = request.model_type
            model_type_map = {1: "generation", 2: "embedding"}
            type_str = model_type_map.get(model_type, "generation")
            
            ok = model_service.switch_model(model_name, type_str)
            if ok:
                return inference_pb2.SwitchModelResponse(success=True, message="模型切换成功")
            else:
                return inference_pb2.SwitchModelResponse(success=False, message="模型切换失败")
        except Exception as e:
            logging.error(f"SwitchModel error: {e}", exc_info=True)
            return inference_pb2.SwitchModelResponse(success=False, message=f"模型切换异常: {e}")


def serve():
    global model_service
    
    logging.info("--- gRPC 服务启动流程开始 ---")
    
    try:
        logging.info("正在初始化 RAGService...")
        model_service = RAGService(model_dir=MODEL_DIR, embed_model_dir=EMBED_MODEL_DIR, db_path=RAG_DB_PATH)
        
        if model_service.generation_model is None:
            logging.critical("严重错误: RAGService 初始化完成，但生成模型未能加载。服务将退出。")
            sys.exit(1)

    except Exception as e:
        logging.critical(f"在服务初始化阶段发生致命错误，无法启动: {e}", exc_info=True)
        sys.exit(1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    
    logging.info("***** gRPC 服务器已成功启动，正在监听端口 50051 *****")
    server.start()
    server.wait_for_termination()
    logging.info("--- gRPC 服务已停止 ---")

if __name__ == '__main__':
    # 我们把 sys.path.append 移到这里，确保它只在作为主脚本运行时执行
    # 并且在使用 os 之前，os 模块已经被导入
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    serve()