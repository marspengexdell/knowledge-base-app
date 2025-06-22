from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    """
    应用配置
    """
    # 项目元数据
    PROJECT_NAME: str = "Knowledge Base App API"
    API_V1_STR: str = "/api/v1"

    # gRPC 服务配置
    INFERENCE_SERVER_URL: str = "localhost:50051"
    GRPC_SERVER: str = "localhost:50051"

    # 模型存储目录（后台上传模型时使用）
    MODEL_DIR: str = "/models"

    # 数据库配置
    DATABASE_URL: Union[str, None] = None

    # CORS 配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # 运行环境
    ENV: str = "development"
