"""
Few-shot 檢索器 (ChromaDB 版本)
使用 ChromaDB 進行持久化和高效檢索
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not installed. Install with: pip install chromadb")


class FewshotRetrieverChroma:
    """使用 ChromaDB 的 Few-shot 檢索器"""
    
    def __init__(
        self,
        fewshot_path: str,
        db_path: str = ".chromadb",
        collection_name: str = "fewshot_examples",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        初始化 ChromaDB 檢索器
        
        Args:
            fewshot_path: fewshot 檔案路徑
            db_path: ChromaDB 資料庫路徑
            collection_name: Collection 名稱
            embedding_model: Embedding 模型名稱
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")
        
        self.fewshot_path = Path(fewshot_path)
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 載入或創建 collection
        self._setup_collection()
    
    def _setup_collection(self):
        """設置 ChromaDB collection"""
        try:
            # 嘗試獲取現有 collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model
                )
            )
            
            # 檢查是否需要更新
            if self._needs_update():
                logging.info("Few-shot data has changed, updating ChromaDB...")
                self._rebuild_collection()
            else:
                logging.info(f"Loaded existing collection with {self.collection.count()} examples")
        
        except Exception:
            # Collection 不存在，創建新的
            logging.info("Creating new ChromaDB collection...")
            self._rebuild_collection()
    
    def _needs_update(self) -> bool:
        """檢查 few-shot 資料是否有更新"""
        # 檢查檔案修改時間
        fewshot_mtime = self.fewshot_path.stat().st_mtime
        
        # 從 collection metadata 獲取上次更新時間
        metadata = self.collection.metadata or {}
        last_update = metadata.get('last_update', 0)
        
        return fewshot_mtime > last_update
    
    def _rebuild_collection(self):
        """重建 collection"""
        # 刪除舊的 collection
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        
        # 創建新的 collection
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            ),
            metadata={
                "last_update": self.fewshot_path.stat().st_mtime,
                "embedding_model": self.embedding_model
            }
        )
        
        # 載入 few-shot 資料
        with open(self.fewshot_path, 'r', encoding='utf-8') as f:
            fewshot_data = json.load(f)
        
        questions = fewshot_data.get('questions', [])
        
        if not questions:
            logging.warning("No few-shot questions found")
            return
        
        # 準備資料
        documents = []
        metadatas = []
        ids = []
        
        for i, q in enumerate(questions):
            question_text = q.get('question', '')
            
            if not question_text:
                continue
            
            documents.append(question_text)
            
            # 提取元數據
            metadata = {
                'question_id': i,
                'db_id': q.get('db_id', ''),
                'has_sql': bool(q.get('prompt', '')),
            }
            
            # 可選：添加更多元數據
            if 'difficulty' in q:
                metadata['difficulty'] = q['difficulty']
            
            metadatas.append(metadata)
            ids.append(str(i))
        
        # 批次添加到 ChromaDB
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logging.info(f"Added {len(documents)} examples to ChromaDB")
    
    def retrieve_top_k(
        self,
        query: str,
        k: int = 1,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[int, float]]:
        """
        檢索最相似的 k 個 few-shot 範例
        
        Args:
            query: 查詢問題
            k: 返回的範例數量
            filter_metadata: 元數據過濾條件（例如 {"difficulty": "easy"}）
            
        Returns:
            List of (question_id, similarity_score)
        """
        # 查詢 ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter_metadata
        )
        
        # 解析結果
        if not results['ids'] or not results['ids'][0]:
            logging.warning("No results found")
            return [(0, 0.0)]
        
        question_ids = [int(id_str) for id_str in results['ids'][0]]
        distances = results['distances'][0]
        
        # 轉換距離為相似度（ChromaDB 返回的是距離，越小越相似）
        # 使用 1 / (1 + distance) 轉換
        similarities = [1 / (1 + d) for d in distances]
        
        results_list = list(zip(question_ids, similarities))
        
        # 記錄結果
        for qid, score in results_list:
            metadata = results['metadatas'][0][results_list.index((qid, score))]
            logging.info(f"Retrieved few-shot #{qid} (similarity: {score:.4f})")
        
        return results_list
    
    def get_best_question_id(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        獲取最佳匹配的 question_id
        
        Args:
            query: 查詢問題
            filter_metadata: 元數據過濾條件
            
        Returns:
            最佳匹配的 question_id
        """
        # 檢查是否需要更新（每次查詢時檢查）
        if self._needs_update():
            logging.info("Few-shot data updated, rebuilding ChromaDB index...")
            self._rebuild_collection()
        
        results = self.retrieve_top_k(query, k=1, filter_metadata=filter_metadata)
        return results[0][0] if results else 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """獲取 collection 統計資訊"""
        count = self.collection.count()
        metadata = self.collection.metadata or {}
        
        return {
            'total_examples': count,
            'embedding_model': metadata.get('embedding_model', 'unknown'),
            'last_update': metadata.get('last_update', 0),
            'collection_name': self.collection_name
        }
    
    def reset(self):
        """重置 collection"""
        logging.info("Resetting ChromaDB collection...")
        self._rebuild_collection()


# 全域快取
_chroma_retriever_cache = {}


def get_chroma_retriever(
    fewshot_path: str,
    db_path: str = ".chromadb",
    collection_name: str = "fewshot_examples"
) -> FewshotRetrieverChroma:
    """
    獲取 ChromaDB 檢索器實例（使用快取）
    
    Args:
        fewshot_path: fewshot 檔案路徑
        db_path: ChromaDB 資料庫路徑
        collection_name: Collection 名稱
        
    Returns:
        FewshotRetrieverChroma 實例
    """
    cache_key = f"{fewshot_path}_{db_path}_{collection_name}"
    
    if cache_key not in _chroma_retriever_cache:
        _chroma_retriever_cache[cache_key] = FewshotRetrieverChroma(
            fewshot_path=fewshot_path,
            db_path=db_path,
            collection_name=collection_name
        )
    
    return _chroma_retriever_cache[cache_key]


# 向後兼容：提供與原始檢索器相同的介面
def get_retriever(fewshot_path: str, model_name: str = "all-MiniLM-L6-v2"):
    """
    向後兼容的檢索器獲取函數
    優先使用 ChromaDB，如果不可用則回退到原始實作
    """
    if CHROMADB_AVAILABLE:
        # 從 fewshot_path 推導 db_path
        fewshot_dir = Path(fewshot_path).parent.parent
        db_path = fewshot_dir / ".chromadb"
        
        return get_chroma_retriever(
            fewshot_path=fewshot_path,
            db_path=str(db_path)
        )
    else:
        # 回退到原始實作
        from runner.fewshot_retriever import get_retriever as get_original_retriever
        return get_original_retriever(fewshot_path, model_name)
