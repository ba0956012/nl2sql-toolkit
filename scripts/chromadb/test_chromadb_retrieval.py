#!/usr/bin/env python3
"""
測試 ChromaDB Few-shot 檢索
"""

import sys
import time
from pathlib import Path
import argparse

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from runner.fewshot_retriever_chroma import FewshotRetrieverChroma, CHROMADB_AVAILABLE
except ImportError:
    CHROMADB_AVAILABLE = False


def test_chromadb(db_root, test_questions):
    """測試 ChromaDB 檢索"""
    
    if not CHROMADB_AVAILABLE:
        print("❌ ChromaDB 未安裝")
        print()
        print("安裝方式:")
        print("  pip install chromadb")
        return False
    
    print("=" * 60)
    print("  ChromaDB Few-shot 檢索測試")
    print("=" * 60)
    print()
    
    # 初始化檢索器
    fewshot_path = Path(db_root) / 'fewshot' / 'questions.json'
    db_path = Path(db_root) / '.chromadb'
    
    if not fewshot_path.exists():
        print(f"❌ 找不到 fewshot 檔案: {fewshot_path}")
        return False
    
    print(f"📂 Few-shot 資料: {fewshot_path}")
    print(f"📂 ChromaDB 路徑: {db_path}")
    print()
    
    # 測試初始化時間
    print("⏱️  測試初始化時間...")
    start = time.time()
    retriever = FewshotRetrieverChroma(
        fewshot_path=str(fewshot_path),
        db_path=str(db_path)
    )
    init_time = time.time() - start
    print(f"   初始化時間: {init_time:.2f}s")
    print()
    
    # 顯示統計資訊
    stats = retriever.get_collection_stats()
    print("📊 Collection 統計:")
    print(f"   總範例數: {stats['total_examples']}")
    print(f"   Embedding 模型: {stats['embedding_model']}")
    print(f"   Collection 名稱: {stats['collection_name']}")
    print()
    
    # 測試檢索
    print("🔍 測試檢索功能:")
    print()
    
    total_time = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"測試 {i}/{len(test_questions)}")
        print(f"問題: {question}")
        print("-" * 60)
        
        # 測試檢索時間
        start = time.time()
        results = retriever.retrieve_top_k(question, k=3)
        query_time = time.time() - start
        total_time += query_time
        
        print(f"檢索時間: {query_time:.4f}s")
        print(f"Top-3 相似範例:")
        
        for rank, (qid, score) in enumerate(results, 1):
            # 讀取原始資料以顯示問題
            import json
            with open(fewshot_path, 'r', encoding='utf-8') as f:
                fewshot_data = json.load(f)
            
            fewshot_q = fewshot_data['questions'][qid].get('question', 'N/A')
            print(f"  {rank}. 範例 #{qid} (相似度: {score:.4f})")
            print(f"     {fewshot_q}")
        
        print()
    
    # 效能總結
    avg_time = total_time / len(test_questions)
    print("=" * 60)
    print("📈 效能總結:")
    print(f"   總查詢時間: {total_time:.2f}s")
    print(f"   平均查詢時間: {avg_time:.4f}s")
    print(f"   每秒查詢數: {1/avg_time:.1f} QPS")
    print("=" * 60)
    print()
    
    return True


def compare_performance(db_root, test_questions):
    """比較 ChromaDB 和原始方案的效能"""
    
    print("=" * 60)
    print("  效能比較測試")
    print("=" * 60)
    print()
    
    fewshot_path = Path(db_root) / 'fewshot' / 'questions.json'
    
    # 測試原始方案
    print("🔵 測試原始方案...")
    try:
        from runner.fewshot_retriever import FewshotRetriever
        
        start = time.time()
        original_retriever = FewshotRetriever(str(fewshot_path))
        original_init = time.time() - start
        
        start = time.time()
        for q in test_questions:
            original_retriever.get_best_question_id(q)
        original_query = time.time() - start
        
        print(f"   初始化: {original_init:.2f}s")
        print(f"   查詢: {original_query:.2f}s")
        print()
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        original_init = None
        original_query = None
    
    # 測試 ChromaDB
    print("🟢 測試 ChromaDB...")
    try:
        from runner.fewshot_retriever_chroma import FewshotRetrieverChroma
        
        db_path = Path(db_root) / '.chromadb'
        
        start = time.time()
        chroma_retriever = FewshotRetrieverChroma(
            fewshot_path=str(fewshot_path),
            db_path=str(db_path)
        )
        chroma_init = time.time() - start
        
        start = time.time()
        for q in test_questions:
            chroma_retriever.get_best_question_id(q)
        chroma_query = time.time() - start
        
        print(f"   初始化: {chroma_init:.2f}s")
        print(f"   查詢: {chroma_query:.2f}s")
        print()
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        chroma_init = None
        chroma_query = None
    
    # 比較結果
    if original_init and chroma_init:
        print("=" * 60)
        print("📊 比較結果:")
        print()
        print(f"初始化加速: {original_init/chroma_init:.1f}x")
        print(f"查詢加速: {original_query/chroma_query:.1f}x")
        print()
        
        if chroma_query < original_query:
            print("✅ ChromaDB 更快！")
        else:
            print("⚠️  原始方案更快（可能是因為範例太少）")
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="測試 ChromaDB Few-shot 檢索")
    parser.add_argument(
        "--db-root",
        type=str,
        default="PosTest",
        help="資料庫根目錄"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="比較 ChromaDB 和原始方案的效能"
    )
    
    args = parser.parse_args()
    
    # 測試問題
    test_questions = [
        "哪個商品賣得最好？",
        "今天的總銷售額是多少？",
        "列出所有庫存低於 10 的商品",
        "查詢所有支付方式",
        "本月新增了幾個客戶？",
        "顯示所有商店的名稱",
    ]
    
    if args.compare:
        compare_performance(args.db_root, test_questions)
    else:
        success = test_chromadb(args.db_root, test_questions)
        
        if success:
            print("✅ 測試完成！")
            print()
            print("下一步:")
            print("  1. 比較效能: python test_chromadb_retrieval.py --compare")
            print("  2. 遷移到 ChromaDB: 參考 CHROMADB_MIGRATION.md")
        else:
            print("❌ 測試失敗")


if __name__ == "__main__":
    main()
