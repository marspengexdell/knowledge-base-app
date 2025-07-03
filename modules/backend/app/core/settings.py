from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Base API"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"

    # gRPC服务器地址，强烈建议仅用一个环境变量
    GRPC_SERVER: str = "inference:50051"  # 默认

    # 模型、数据库等路径
    MODEL_DIR: str = "/models"
    DATABASE_URL: Union[str, None] = None

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:8081"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
