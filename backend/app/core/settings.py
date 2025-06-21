from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Base API"
    ENV: str = "development"

    GRPC_SERVER_HOST: str = "localhost"
    GRPC_SERVER_PORT: int = 50051
    # 支持字符串形式的 SERVER
    GRPC_SERVER: str = "localhost:50051"
    INFERENCE_SERVER_URL: str = "localhost:50051"

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:8081"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
