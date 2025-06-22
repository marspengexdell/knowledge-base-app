# 文件：backend/app/api/endpoints/admin.py

from fastapi import APIRouter
import grpc
from ...core.config import settings
from ...protos import inference_pb2, inference_pb2_grpc

router = APIRouter()

@router.post("/models/switch")
def switch_model(data: dict):
    model_name = data.get("model_name")
    model_type = data.get("model_type", "generation")
    # 将模型类型映射为 gRPC 中的枚举
    type_enum = inference_pb2.GENERATION if model_type == "generation" else inference_pb2.EMBEDDING
    # 调用 gRPC 服务切换模型
    channel = grpc.insecure_channel(settings.GRPC_SERVER)
    stub = inference_pb2_grpc.InferenceServiceStub(channel)
    try:
        resp = stub.SwitchModel(inference_pb2.SwitchModelRequest(model_name=model_name, model_type=type_enum))
        return {"success": resp.success, "message": resp.message}
    except Exception as e:
        return {"success": False, "message": f"模型切换失败: {e}"}

@router.get("/models")
def list_models():
    # 调用 gRPC 服务获取模型列表
    channel = grpc.insecure_channel(settings.GRPC_SERVER)
    stub = inference_pb2_grpc.InferenceServiceStub(channel)
    try:
        resp = stub.ListAvailableModels(inference_pb2.Empty())
        return {
            "generation_models": list(resp.generation_models),
            "embedding_models": list(resp.embedding_models),
            "current_generation_model": resp.current_generation_model,
            "current_embedding_model": resp.current_embedding_model
        }
    except Exception as e:
        # 如果调用失败，返回空列表
        return {"generation_models": [], "embedding_models": [], "current_generation_model": "", "current_embedding_model": ""}
