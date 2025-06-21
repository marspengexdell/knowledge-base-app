import os
from typing import List, Dict, Optional
from .model_service import ModelService

# 假定知识库文档简单保存在文本文件，或后续可对接 ChromaDB
KNOWLEDGE_DIR = "/data/knowledge"   # 文档存放路径

class RAGService:
    def __init__(self, model_dir: str, knowledge_dir: Optional[str] = None):
        self.model_service = ModelService(model_dir)
        self.knowledge_dir = knowledge_dir or KNOWLEDGE_DIR

    def _load_knowledge_texts(self) -> List[str]:
        """读取知识库文档（简单文本文件，每行一条）"""
        kb_file = os.path.join(self.knowledge_dir, "knowledge.txt")
        if not os.path.exists(kb_file):
            return []
        with open(kb_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        模拟知识检索：对所有文档做 embedding，和 query 余弦距离排序取前k条
        实际生产应用 ChromaDB/FAISS/vector DB
        """
        docs = self._load_knowledge_texts()
        if not docs:
            return []
        # embedding query
        query_emb = self.model_service.embed(query)
        if not query_emb:
            return []
        # embedding docs
        doc_scores = []
        for doc in docs:
            doc_emb = self.model_service.embed(doc)
            # 简单余弦相似度
            score = self._cosine_sim(query_emb, doc_emb)
            doc_scores.append((score, doc))
        doc_scores.sort(reverse=True)
        return [doc for score, doc in doc_scores[:top_k]]

    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        """余弦相似度"""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        if not a.any() or not b.any():
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def generate_with_knowledge(self, query: str) -> str:
        """
        RAG主流程：知识检索 + prompt拼接 + 大模型生成
        """
        retrieved = self.search(query, top_k=3)
        knowledge = "\n".join(retrieved)
        prompt = f"基于以下资料内容回答：\n{knowledge}\n用户问题：{query}"
        return self.model_service.generate(prompt)

# 单例（如果需要可以全局用）
# rag_service = RAGService(model_dir="/models", knowledge_dir="/data/knowledge")

