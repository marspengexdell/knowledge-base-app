# 文件：inference/app/server.py

import grpc
from concurrent import futures
import logging
from protos import inference_pb2, inference_pb2_grpc
from services.model_service import RAGService

MODEL_DIR = "/models"
EMBED_MODEL_DIR = "/models/embedding-model/bge-base-zh"
RAG_DB_PATH = "/app/vector_db.pkl"

model_service = RAGService(model_dir=MODEL_DIR, embed_model_dir=EMBED_MODEL_DIR, db_path=RAG_DB_PATH)

class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def ChatStream(self, request, context):
        prompt = request.query
        session_id = getattr(request, 'session_id', "")
        try:
            kb_chunks = model_service.query(prompt, topk=3)
            if kb_chunks:
                kb_texts = [chunk["text"] for chunk in kb_chunks]
                rag_prompt = "检索到的知识片段：\n" + "\n---\n".join(kb_texts) + f"\n\n用户问题：{prompt}"
            else:
                rag_prompt = f"用户问题：{prompt}"

            logging.info(f"[RAG PROMPT]\n{rag_prompt}")
            sent_token = False
            for token in model_service.generate_stream(rag_prompt):
                if token is not None:
                    sent_token = True
                    yield inference_pb2.ChatResponse(token=token)
            if not sent_token:
                yield inference_pb2.ChatResponse(error_message="模型无输出，请检查模型或输入。")
            yield inference_pb2.ChatResponse(token="[DONE]")
        except Exception as e:
            logging.error(f"ChatStream error: {e}", exc_info=True)
            yield inference_pb2.ChatResponse(error_message=f"服务端异常: {e}")

    def ListAvailableModels(self, request, context):
        try:
            models = model_service.list_models()
            return inference_pb2.ModelListResponse(
                generation_models=models.get("generation_models", []),
                embedding_models=models.get("embedding_models", []),
                current_generation_model=models.get("current_generation_model", ""),
                current_embedding_model=models.get("current_embedding_model", "")
            )
        except Exception as e:
            logging.error(f"ListAvailableModels error: {e}", exc_info=True)
            return inference_pb2.ModelListResponse()

    def SwitchModel(self, request, context):
        try:
            model_name = request.model_name
            model_type = request.model_type  # int
            model_type_map = {1: "generation", 2: "embedding"}
            type_str = model_type_map.get(model_type, "generation")
            # 异步后台加载模型
            model_service.switch_model(model_name, type_str)
            return inference_pb2.SwitchModelResponse(success=True, message="模型切换成功")
        except Exception as e:
            logging.error(f"SwitchModel error: {e}", exc_info=True)
            return inference_pb2.SwitchModelResponse(success=False, message=f"模型切换异常: {e}")

def serve():
    logging.basicConfig(level=logging.INFO)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
