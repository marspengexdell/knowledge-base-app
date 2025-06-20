from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    Utilizes Pydantic's BaseSettings to automatically read and validate
    configuration from the environment or a .env file.
    """
    # --- Project Metadata ---
    PROJECT_NAME: str = "Knowledge Base App API"
    API_V1_STR: str = "/api/v1"

    # --- gRPC Server Configuration ---
    # 兼容 env 的 GRPC_SERVER 字段（可用于回滚老配置）
    INFERENCE_SERVER_URL: str = "localhost:50051"
    GRPC_SERVER: str = "localhost:50051"

    # --- Database Configuration ---
    DATABASE_URL: Union[str, None] = None

    # --- CORS 配置 ---
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # --- 运行环境（兼容 .env）---
    ENV: str = "development"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",  # 忽略未声明的字段（推荐Pydantic2方式）
    }

# Create a single instance of the settings object to be imported by other modules.
settings = Settings()
