import os
import logging
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_chat_handler(model_path: str):
    """
    自动根据模型元数据获取聊天处理器，无需外部配置文件。
    """
    logger.info(f"正在为模型 '{os.path.basename(model_path)}' 自动检测聊天模板...")
    try:
        # 只轻量读取元数据
        llama = Llama(model_path=model_path, n_ctx=256, n_gpu_layers=0, verbose=False)
        chat_template = llama.metadata.get("tokenizer.chat_template")
        if chat_template:
            logger.info("成功从模型元数据中提取到聊天模板")
            chat_handler = llama.chat_handler_from_template(chat_template)
            del llama
            return chat_handler
        logger.warning("未找到聊天模板，无法自动处理聊天格式。")
        del llama
        return None
    except Exception as e:
        logger.error(f"读取模型元数据失败: {e}", exc_info=True)
        return None
