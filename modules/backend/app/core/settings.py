from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Base API"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"

    # 推荐：支持docker-compose里的GRPC_SERVER_ADDRESS，优先使用环境变量
    GRPC_SERVER: str = (
        os.environ.get("GRPC_SERVER_ADDRESS")
        or os.environ.get("GRPC_SERVER")
        or "localhost:50051"
    )

    GRPC_SERVER_HOST: str = "localhost"
    GRPC_SERVER_PORT: int = 50051
    INFERENCE_SERVER_URL: str = "localhost:50051"

    MODEL_DIR: str = "/models"
    DATABASE_URL: Union[str, None] = None

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:8081"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
