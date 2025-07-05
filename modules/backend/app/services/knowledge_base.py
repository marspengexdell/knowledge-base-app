import os
import logging
import uuid
from typing import List, Optional, Dict
from langchain_core.documents import Document
from core.db_client import vector_db
from services.embedding import embedding_model

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = storage_dir or os.getenv("KNOWLEDGE_BASE_DOCS", "/knowledge_base_docs")
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Knowledge base storage directory: {self.storage_dir}")

    def add_document(self, file_name: str, file_data: bytes) -> str:
        doc_id = str(uuid.uuid4())
        file_path = os.path.join(self.storage_dir, doc_id + ".txt")
        with open(file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"Document '{file_name}' saved as '{file_path}' with UUID {doc_id}")
        return doc_id

    async def embed_document(self, doc_id: str, original_name: str) -> bool:
        file_path = os.path.join(self.storage_dir, doc_id + ".txt")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)

        with open(file_path, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("gbk", errors="ignore")

        doc = Document(page_content=text, metadata={"id": doc_id, "source": original_name})
        embedding = await embedding_model.embed(text)
        await vector_db.add_documents([doc], [embedding], doc_id)
        logger.info(f"Document '{doc_id}' embedded and stored")
        return True

    async def delete_documents_by_id(self, doc_id: str) -> bool:
        file_path = os.path.join(self.storage_dir, doc_id + ".txt")
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        try:
            vector_db.delete_documents_by_source(doc_id)
        except Exception:
            logger.warning("Failed to delete document from vector DB", exc_info=True)
        logger.info(f"Document '{doc_id}' deleted")
        return True

    def _load_doc_meta(self) -> List[Dict]:
        docs = []
        for file in os.listdir(self.storage_dir):
            if not file.endswith(".txt"):
                continue
            doc_id = file.replace(".txt", "")
            path = os.path.join(self.storage_dir, file)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(5000)
                preview = content.strip().replace('\n', '').replace('\r', '')
                preview = preview[:50] + '...' if len(preview) > 50 else preview
                docs.append({"id": doc_id, "title": file, "content": preview})
        return docs

    async def paginated_list(self, page: int, page_size: int, search: str, by: str):
        all_docs = self._load_doc_meta()
        if search:
            def match(doc):
                s = search.lower()
                return (s in doc["title"].lower() if by in ("title", "all") else False) or \
                       (s in doc["content"].lower() if by in ("content", "all") else False)
            all_docs = [doc for doc in all_docs if match(doc)]
        all_docs.sort(key=lambda d: d["title"])
        total = len(all_docs)
        start = (page - 1) * page_size
        end = start + page_size
        page_docs = all_docs[start:end]
        return {"total": total, "docs": page_docs}

    async def search(self, query: str, n_results: int = 3) -> List[Document]:
        try:
            results = await vector_db.asimilarity_search(query, k=n_results)
            return results
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}", exc_info=True)
            return []

kb_service = KnowledgeBaseService()
