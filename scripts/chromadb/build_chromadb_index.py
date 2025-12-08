#!/usr/bin/env python3
"""
建立 ChromaDB 索引
"""

import sys
import os
import argparse
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))


def build_index(db_root):
    """建立 ChromaDB 索引"""
    
    print("=" * 60)
    print("  建立 ChromaDB 索引")
    print("=" * 60)
    print()
    
    fewshot_path = Path(db_root) / 'fewshot' / 'questions.json'
    db_path = Path(db_root) / '.chromadb'
    
    # 檢查 fewshot 檔案
    if not fewshot_path.exists():
        print(f"❌ 找不到 fewshot 檔案: {fewshot_path}")
        return False
    
    print(f"📂 Few-shot 資料: {fewshot_path}")
    print(f"📂 ChromaDB 路徑: {db_path}")
    print()
    
    try:
        from runner.fewshot_retriever_chroma import get_chroma_retriever
        
        print("🔍 建立索引...")
        retriever = get_chroma_retriever(str(fewshot_path), str(db_path))
        
        stats = retriever.get_collection_stats()
        
        print()
        print("✅ ChromaDB 索引已建立")
        print(f"   總範例數: {stats['total_examples']}")
        print(f"   Embedding 模型: {stats['embedding_model']}")
        print(f"   Collection: {stats['collection_name']}")
        print()
        
        return True
        
    except ImportError:
        print("⚠️  ChromaDB 未安裝")
        print()
        print("安裝方式:")
        print("  pip install chromadb")
        print()
        print("系統仍可使用，但檢索速度較慢")
        return False
        
    except Exception as e:
        print(f"❌ 索引建立失敗: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("系統仍可使用，但檢索速度較慢")
        return False


def main():
    parser = argparse.ArgumentParser(description="建立 ChromaDB 索引")
    parser.add_argument(
        "--db-root",
        type=str,
        required=True,
        help="資料庫根目錄"
    )
    
    args = parser.parse_args()
    
    success = build_index(args.db_root)
    
    if success:
        print("=" * 60)
        print("  完成")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
