import os
import logging
from typing import List
from langchain_core.documents import Document

from core.db_client import vector_db
from services.embedding import embedding_model

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge base documents."""

    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = storage_dir or os.getenv("KNOWLEDGE_BASE_DOCS", "/knowledge_base_docs")
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Knowledge base storage directory: {self.storage_dir}")

    def add_document(self, file_name: str, file_data: bytes) -> bool:
        """Save an uploaded document to disk."""
        file_path = os.path.join(self.storage_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"Document '{file_name}' saved to '{file_path}'")
        return True

    async def embed_document(self, file_name: str) -> bool:
        """Embed a stored document and add it to the vector database."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)

        with open(file_path, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("gbk", errors="ignore")

        doc = Document(page_content=text, metadata={"source": file_name})
        embedding = await embedding_model.embed(text)
        await vector_db.add_documents([doc], [embedding], file_name)
        logger.info(f"Document '{file_name}' embedded and stored")
        return True

    def list_documents(self) -> List[str]:
        """Return a list of filenames stored in the knowledge base directory."""
        return [
            f
            for f in os.listdir(self.storage_dir)
            if os.path.isfile(os.path.join(self.storage_dir, f))
        ]

    async def list_all_documents(self) -> List[dict] | None:
        """List all documents stored in the vector database."""
        try:
            results = vector_db.collection.get(include=["metadatas"], limit=None)
            sources: List[dict] = []
            seen: set[str] = set()
            for meta in results.get("metadatas", []):
                src = meta.get("source")
                if src and src not in seen:
                    seen.add(src)
                    sources.append({"source": src})
            return sources
        except Exception as e:
            logger.error(f"Failed to list documents: {e}", exc_info=True)
            return None

    def delete_document(self, file_name: str) -> bool:
        """Delete a document from disk and the vector store."""
        file_path = os.path.join(self.storage_dir, file_name)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        try:
            vector_db.delete_documents_by_source(file_name)
        except Exception:
            logger.warning("Failed to delete document from vector DB", exc_info=True)
        logger.info(f"Document '{file_name}' deleted")
        return True

    async def delete_documents_by_source(self, source_name: str) -> bool:
        """Asynchronously delete all vectors related to the given source."""
        return self.delete_document(source_name)

    async def add_documents(self, documents: List[Document], document_source: str) -> None:
        """Add a batch of documents with embeddings to the vector database."""
        if not documents:
            return
        try:
            texts = [d.page_content for d in documents]
            embeddings = await embedding_model.embed_batch(texts)
            await vector_db.add_documents(documents, embeddings, document_source)
            logger.info(f"Added {len(documents)} documents from '{document_source}'")
        except Exception as e:
            logger.error(f"Error adding documents: {e}", exc_info=True)
            raise

    async def search(self, query: str, n_results: int = 3) -> List[Document]:
        """Search the knowledge base for relevant documents."""
        try:
            query_embedding = await embedding_model.embed(query)
            if not query_embedding:
                return []
            results = await vector_db.search_with_vector(query_embedding, top_k=n_results)
            logger.info(f"Found {len(results)} documents for query '{query}'")
            return results
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}", exc_info=True)
            return []


kb_service = KnowledgeBaseService()
