import grpc
from concurrent import futures
from protos import inference_pb2, inference_pb2_grpc
from services.model_service import ModelService
from services.rag_service import RAGService   # 新增

MODEL_DIR = "/app/models"
RAG_DB_PATH = "/app/vector_db.pkl"
EMBED_MODEL_PATH = "/app/models"  # 或填某embedding模型名
model_service = ModelService(MODEL_DIR)
rag_service = RAGService(embed_model_dir=EMBED_MODEL_PATH, db_path=RAG_DB_PATH)

class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def ChatStream(self, request, context):
        prompt = request.query
        # RAG召回
        kb_chunks = rag_service.query(prompt, topk=3)
        rag_prompt = "检索到的知识片段：\n" + "\n---\n".join(kb_chunks) + f"\n\n用户问题：{prompt}"
        for token in model_service.generate_stream(rag_prompt):
            if token.strip():
                yield inference_pb2.ChatResponse(token=token)
        yield inference_pb2.ChatResponse(token="[DONE]")

    def ListAvailableModels(self, request, context):
        models = model_service.list_models()
        return inference_pb2.ModelListResponse(
            generation_models=models.get("generation_models", []),
            embedding_models=models.get("embedding_models", []),
            current_generation_model=models.get("current_generation_model", ""),
            current_embedding_model=models.get("current_embedding_model", "")
        )

    def SwitchModel(self, request, context):
        model_name = request.model_name
        model_type = request.model_type  # int
        model_type_map = {1: "generation", 2: "embedding"}
        type_str = model_type_map.get(model_type, "generation")
        ok = model_service.load_model(model_name, type_str)
        if ok:
            return inference_pb2.SwitchModelResponse(success=True, message="模型切换成功")
        else:
            return inference_pb2.SwitchModelResponse(success=False, message="模型切换失败")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
