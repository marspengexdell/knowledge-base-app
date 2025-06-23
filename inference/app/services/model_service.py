import os
import logging
from llama_cpp import Llama

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGService:
    def __init__(self, model_dir, embed_model_dir, db_path):
        """
        初始化模型服务。
        """
        logging.info("--- RAGService 初始化开始 ---")
        self.model_dir = model_dir
        self.embed_model_dir = embed_model_dir
        self.db_path = db_path
        
        self.generation_model = None
        self.embedding_model = None
        
        self.current_generation_model_name = None
        self.current_embedding_model_name = None

        self.load_or_die()
        logging.info("--- RAGService 初始化完成 ---")

    def find_model_path(self, model_name, directory):
        """在指定目录中查找模型文件的完整路径。"""
        if not model_name:
            return None
        
        path = os.path.join(directory, model_name)
        if os.path.exists(path):
            logging.info(f"成功找到模型文件: {path}")
            return path
        
        logging.warning(f"模型文件未找到: {path}")
        return None

    def load_generation_model(self):
        """加载或重新加载生成模型，这是启用GPU的关键。"""
        if not self.current_generation_model_name:
            logging.error("没有设置当前的生成模型名称，无法加载。")
            return

        model_path = self.find_model_path(self.current_generation_model_name, self.model_dir)
        if not model_path:
            logging.error(f"无法加载生成模型，因为路径不存在: {self.current_generation_model_name}")
            return

        logging.info(f"开始从路径加载生成模型: {model_path}")
        try:
            self.generation_model = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                n_ctx=4096,
                verbose=True
            )
            logging.info(f"***** 已成功加载并启用GPU模型: {self.current_generation_model_name} *****")
        except Exception as e:
            logging.error(f"加载模型 {model_path} 时发生严重错误: {e}", exc_info=True)
            self.generation_model = None

    def list_models(self):
        """列出模型目录中所有可用的 GGUF 模型文件。"""
        logging.info(f"正在扫描模型目录: {self.model_dir}")
        generation_models = []
        embedding_models = []
        
        try:
            if not os.path.exists(self.model_dir):
                 logging.error(f"模型目录不存在: {self.model_dir}")
                 return {}, {}
            
            for filename in os.listdir(self.model_dir):
                if filename.lower().endswith(".gguf"):
                    generation_models.append(filename)
            logging.info(f"找到 {len(generation_models)} 个生成模型: {generation_models}")
            
        except Exception as e:
            logging.error(f"扫描模型目录时出错: {e}", exc_info=True)

        return generation_models, embedding_models

    def load_or_die(self):
        """
        执行服务启动时的模型发现和加载流程。
        """
        gen_models, _ = self.list_models()
        if not gen_models:
            logging.error("错误：在 /models 目录中没有找到任何 .gguf 模型文件。服务无法启动。")
            # 在实际生产中，这里可以直接 raise Exception("No models found") 来中断启动
            return
            
        self.current_generation_model_name = gen_models[0]
        logging.info(f"默认选择加载模型: {self.current_generation_model_name}")
        self.load_generation_model()

    def generate_stream(self, prompt):
        """使用加载的模型生成文本流。"""
        if not self.generation_model:
            logging.error("生成请求失败，因为模型未成功加载。")
            yield "模型未加载，请检查服务端日志。"
            return
        # ... (其余代码不变)
        try:
            stream = self.generation_model.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for output in stream:
                token = output["choices"][0]["delta"].get("content")
                if token:
                    yield token
        except Exception as e:
            logging.error(f"文本生成时出错: {e}", exc_info=True)
            yield f"文本生成时遇到错误: {e}"