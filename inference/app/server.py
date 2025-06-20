import grpc
from concurrent import futures
import time
from protos import inference_pb2, inference_pb2_grpc

from services.model_service import ModelService

MODEL_DIR = "/app/models"
model_service = ModelService(MODEL_DIR)

class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def ChatStream(self, request, context):
        # 正确用法：只赋值 oneof 中的一个字段
        for i in range(3):
            yield inference_pb2.ChatResponse(token=f"回复分片 {i+1}")
            time.sleep(0.2)
        # 结束标志，也只赋值 token
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
        model_type = request.model_type
        ok = model_service.load_model(model_name, model_type)
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
