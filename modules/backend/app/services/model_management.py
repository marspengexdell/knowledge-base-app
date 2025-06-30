import os
import logging

logger = logging.getLogger(__name__)

class ModelManagementService:
    def __init__(self, storage_dir: str = "model_storage"):
        """
        初始化模型管理服务。
        :param storage_dir: 存放上传模型文件的目录名。
        """
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"模型存储目录 '{self.storage_dir}' 已创建。")

    def add_model(self, filename: str, file_data: bytes) -> str:
        """
        将上传的模型文件保存到本地。
        """
        file_path = os.path.join(self.storage_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"模型文件 '{filename}' 已保存到 '{file_path}'。")
        return file_path

    def list_models(self) -> list[str]:
        """
        列出所有已上传的模型文件。
        """
        if not os.path.exists(self.storage_dir):
            return []
        # 只返回文件名，不包括路径
        return [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]

# 创建一个全局单例
model_service = ModelManagementService()
