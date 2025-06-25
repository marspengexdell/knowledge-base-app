import json
import os
from llama_cpp import Llama

MODELS_PATH = "/models/"
CONFIG_PATH = "/app/model_config.json"

def get_chat_format(model_path, config_path=CONFIG_PATH):
    """
    自动根据模型元数据+配置，判断chat_format
    """
    # 读取 chat_format 配置
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        model_chat_formats = config.get("model_chat_formats", {})
        default_chat_format = config.get("default_chat_format", "llama-2")
    else:
        model_chat_formats = {"llama": "llama-2"}
        default_chat_format = "llama-2"

    try:
        temp_llama = Llama(model_path=model_path, n_ctx=256, n_gpu_layers=0, verbose=False)
        metadata = temp_llama.metadata
        architecture = metadata.get('general.architecture')
        del temp_llama

        if architecture and architecture in model_chat_formats:
            return model_chat_formats[architecture]
        else:
            return default_chat_format
    except Exception as e:
        return default_chat_format
