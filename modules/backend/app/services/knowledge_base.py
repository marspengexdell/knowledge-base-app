import logging
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 核心修正：将 '...' 改为 '..'，修正了错误的相对导入路径
from ..core.db_client import vector_db
from .embedding import embedding_model

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, storage_dir: str = "document_storage"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def add_document(self, filename: str, file_data: bytes):
        file_path = os.path.join(self.storage_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path

    async def embed_document(self, filename: str):
        file_path = os.path.join(self.storage_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 '{filename}' 不存在。")

        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif filename.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')

        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        text_chunks = text_splitter.split_documents(documents)
        
        batch_size = 32
        logger.info(f"文档 '{filename}' 被切分为 {len(text_chunks)} 个片段，将以每批 {batch_size} 个进行处理。")

        for i in range(0, len(text_chunks), batch_size):
            batch_chunks = text_chunks[i:i + batch_size]
            batch_texts = [chunk.page_content for chunk in batch_chunks]
            
            logger.info(f"正在处理第 {i // batch_size + 1} 批...")
            embeddings = await embedding_model.embed_batch(batch_texts)
            
            await vector_db.add_documents(
                documents=batch_chunks,
                embeddings=embeddings,
                document_source=filename
            )
        
        logger.info(f"文档 '{filename}' 的所有片段都已成功学习并存入数据库。")

    def list_documents(self):
        return [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]

    def delete_document(self, filename: str) -> bool:
        file_path = os.path.join(self.storage_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            vector_db.delete_documents_by_source(filename)
            logger.info(f"已从本地和向量数据库中删除文档: {filename}")
            return True
        return False

    def search(self, query: str, top_k: int = 3):
        return vector_db.search(query=query, top_k=top_k)

kb_service = KnowledgeBaseService()
