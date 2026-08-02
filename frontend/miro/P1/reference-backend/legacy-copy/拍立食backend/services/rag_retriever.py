"""
香疯了 - RAG 检索服务（香了路线）
=================================
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class RAGRetriever:
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.recipes = None

    def load(self, index_path: str, meta_path: str):
        print(f"⏳ 加载 embedding 模型: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            self.recipes = json.load(f)
        print(f"✅ RAG 检索器加载完成: {self.index.ntotal} 条菜谱")

    def search(self, ingredients: list[str], top_k: int = 5) -> list[dict]:
        """输入食材列表，返回最匹配的菜谱"""
        query_text = " ".join(ingredients)
        query_vec = self.model.encode(
            [query_text], normalize_embeddings=True
        ).astype("float32")

        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            recipe = self.recipes[idx].copy()
            recipe["similarity_score"] = round(float(score), 3)
            results.append(recipe)

        return results
