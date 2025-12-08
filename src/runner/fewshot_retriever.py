"""
Few-shot 檢索器
根據問題相似度選擇最合適的 few-shot 範例
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import logging


class FewshotRetriever:
    """Few-shot 範例檢索器"""
    
    def __init__(self, fewshot_path: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化檢索器
        
        Args:
            fewshot_path: fewshot 檔案路徑
            model_name: Sentence Transformer 模型名稱
        """
        self.fewshot_path = Path(fewshot_path)
        self.model = SentenceTransformer(model_name)
        self.fewshot_data = None
        self.question_embeddings = None
        
        self._load_fewshot()
        self._compute_embeddings()
    
    def _load_fewshot(self):
        """載入 fewshot 資料"""
        with open(self.fewshot_path, 'r', encoding='utf-8') as f:
            self.fewshot_data = json.load(f)
        
        logging.info(f"Loaded {len(self.fewshot_data.get('questions', []))} few-shot examples")
    
    def _compute_embeddings(self):
        """計算所有 few-shot 問題的 embeddings"""
        questions = self.fewshot_data.get('questions', [])
        
        if not questions:
            logging.warning("No few-shot questions found")
            self.question_embeddings = np.array([])
            return
        
        # 提取所有問題文本
        question_texts = [q.get('question', '') for q in questions]
        
        # 計算 embeddings
        logging.info("Computing embeddings for few-shot questions...")
        self.question_embeddings = self.model.encode(
            question_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        logging.info(f"Computed embeddings shape: {self.question_embeddings.shape}")
    
    def retrieve_top_k(self, query: str, k: int = 1) -> List[Tuple[int, float]]:
        """
        檢索最相似的 k 個 few-shot 範例
        
        Args:
            query: 查詢問題
            k: 返回的範例數量
            
        Returns:
            List of (question_id, similarity_score)
        """
        if self.question_embeddings.size == 0:
            logging.warning("No embeddings available, returning default question_id=0")
            return [(0, 0.0)]
        
        # 計算查詢的 embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        )[0]
        
        # 計算相似度（cosine similarity）
        similarities = np.dot(self.question_embeddings, query_embedding) / (
            np.linalg.norm(self.question_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # 獲取 top-k
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        top_k_scores = similarities[top_k_indices]
        
        results = [(int(idx), float(score)) for idx, score in zip(top_k_indices, top_k_scores)]
        
        # 記錄結果
        for idx, score in results:
            question = self.fewshot_data['questions'][idx].get('question', 'N/A')
            logging.info(f"Retrieved few-shot #{idx} (similarity: {score:.4f}): {question[:80]}...")
        
        return results
    
    def get_best_question_id(self, query: str) -> int:
        """
        獲取最佳匹配的 question_id
        
        Args:
            query: 查詢問題
            
        Returns:
            最佳匹配的 question_id
        """
        results = self.retrieve_top_k(query, k=1)
        return results[0][0] if results else 0


# 全域快取，避免重複載入
_retriever_cache = {}


def get_retriever(fewshot_path: str, model_name: str = "all-MiniLM-L6-v2") -> FewshotRetriever:
    """
    獲取 FewshotRetriever 實例（使用快取）
    
    Args:
        fewshot_path: fewshot 檔案路徑
        model_name: 模型名稱
        
    Returns:
        FewshotRetriever 實例
    """
    cache_key = f"{fewshot_path}_{model_name}"
    
    if cache_key not in _retriever_cache:
        _retriever_cache[cache_key] = FewshotRetriever(fewshot_path, model_name)
    
    return _retriever_cache[cache_key]
