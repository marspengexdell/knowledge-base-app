import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self, embed_model_dir: str = None, db_path: str = None):
        self.text_chunks = []
        self.index = None
        self.db_path = db_path
        self.embedder = None
        if embed_model_dir and os.path.exists(embed_model_dir):
            try:
                self.embedder = SentenceTransformer(embed_model_dir)
            except Exception as e:
                print(f"[WARN] 加载embedding模型失败: {e}")
        if db_path:
            self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                self.text_chunks, vecs = pickle.load(f)
                if len(vecs) == 0:
                    self.index = None
                    return
                d = len(vecs[0])
                self.index = faiss.IndexFlatL2(d)
                self.index.add(vecs)
        else:
            self.index = None
            self.text_chunks = []

    def ingest(self, txt_file: str):
        if self.embedder is None:
            print("[WARN] 未加载embedding模型，无法ingest文档")
            return 0
        with open(txt_file, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = [text[i:i+200] for i in range(0, len(text), 200)]
        try:
            emb = self.embedder.encode(chunks, show_progress_bar=True)
        except Exception as e:
            print(f"[ERR] 文本embedding失败: {e}")
            return 0
        if self.index is None:
            self.index = faiss.IndexFlatL2(emb.shape[1])
            self.text_chunks = []
        self.index.add(emb)
        self.text_chunks.extend(chunks)
        # 注意这里保存emb（向量）更好，reconstruct_n只适合Flat索引
        with open(self.db_path, "wb") as f:
            pickle.dump((self.text_chunks, emb), f)
        return len(chunks)

    def query(self, query: str, topk=3):
        if self.index is None or self.embedder is None or not self.text_chunks:
            return []
        try:
            q_emb = self.embedder.encode([query])
            D, I = self.index.search(q_emb, topk)
            results = []
            for idx, score in zip(I[0], D[0]):
                if idx < 0 or idx >= len(self.text_chunks):
                    continue
                results.append({"text": self.text_chunks[idx], "score": float(score)})
            return results
        except Exception as e:
            print(f"[ERR] 检索失败: {e}")
            return []

# 空实现
class DummyRAGService:
    def __init__(self, *args, **kwargs):
        pass
    def ingest(self, txt_file: str):
        print("[INFO] 未启用知识库，ingest操作跳过")
        return 0
    def query(self, query: str, topk=3):
        print("[INFO] 未启用知识库，query返回空")
        return []

# 工厂模式
def get_rag_service(embed_model_dir, db_path):
    if not (embed_model_dir and os.path.exists(embed_model_dir)):
        return DummyRAGService()
    return RAGService(embed_model_dir, db_path)
