import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self, embed_model_dir: str, db_path: str):
        # 用embedding模型
        self.embedder = SentenceTransformer(embed_model_dir)
        self.db_path = db_path
        self.index = None
        self.text_chunks = []  # 源片段
        self._load_db()

    def _load_db(self):
        # 启动时加载
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                self.text_chunks, vecs = pickle.load(f)
                d = len(vecs[0])
                self.index = faiss.IndexFlatL2(d)
                self.index.add(vecs)
        else:
            self.index = None
            self.text_chunks = []

    def ingest(self, txt_file: str):
        # 导入文档
        with open(txt_file, "r", encoding="utf-8") as f:
            text = f.read()
        # 简单按段/每200字切
        chunks = [text[i:i+200] for i in range(0, len(text), 200)]
        emb = self.embedder.encode(chunks)
        # 构建向量库
        if self.index is None:
            self.index = faiss.IndexFlatL2(emb.shape[1])
            self.text_chunks = []
        self.index.add(emb)
        self.text_chunks.extend(chunks)
        # 保存
        with open(self.db_path, "wb") as f:
            pickle.dump((self.text_chunks, self.index.reconstruct_n(0, self.index.ntotal)), f)
        return len(chunks)

    def query(self, query: str, topk=3):
        q_emb = self.embedder.encode([query])
        D, I = self.index.search(q_emb, topk)
        results = [self.text_chunks[i] for i in I[0]]
        return results
