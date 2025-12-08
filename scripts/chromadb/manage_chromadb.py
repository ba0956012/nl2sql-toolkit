#!/usr/bin/env python3
"""
ChromaDB 管理工具
"""

import sys
import os
import argparse
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from runner.fewshot_retriever_chroma import get_chroma_retriever, CHROMADB_AVAILABLE
except ImportError:
    CHROMADB_AVAILABLE = False


def show_stats(db_root):
    """顯示 ChromaDB 統計資訊"""
    if not CHROMADB_AVAILABLE:
        print("❌ ChromaDB 未安裝")
        print("   安裝方式: pip install chromadb")
        return
    
    fewshot_path = Path(db_root) / 'fewshot' / 'questions.json'
    db_path = Path(db_root) / '.chromadb'
    
    try:
        retriever = get_chroma_retriever(str(fewshot_path), str(db_path))
        stats = retriever.get_collection_stats()
        
        print("=" * 60)
        print("  ChromaDB 統計資訊")
        print("=" * 60)
        print()
        print(f"📊 總範例數: {stats['total_examples']}")
        print(f"🤖 Embedding 模型: {stats['embedding_model']}")
        print(f"📦 Collection 名稱: {stats['collection_name']}")
        print(f"📁 資料庫路徑: {db_path}")
        print()
        
        # 檢查磁碟使用
        if db_path.exists():
            import subprocess
            result = subprocess.run(['du', '-sh', str(db_path)], capture_output=True, text=True)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"💾 磁碟使用: {size}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def rebuild(db_root):
    """重建 ChromaDB 索引"""
    if not CHROMADB_AVAILABLE:
        print("❌ ChromaDB 未安裝")
        return
    
    fewshot_path = Path(db_root) / 'fewshot' / 'questions.json'
    db_path = Path(db_root) / '.chromadb'
    
    print("🔄 重建 ChromaDB 索引...")
    
    try:
        retriever = get_chroma_retriever(str(fewshot_path), str(db_path))
        retriever.reset()
        
        stats = retriever.get_collection_stats()
        print(f"✅ 重建完成: {stats['total_examples']} 個範例")
        
    except Exception as e:
        print(f"❌ 重建失敗: {e}")


def clean(db_root):
    """清理 ChromaDB 資料"""
    db_path = Path(db_root) / '.chromadb'
    
    if not db_path.exists():
        print("⚠️  ChromaDB 資料不存在")
        return
    
    import shutil
    
    print(f"🗑️  清理 ChromaDB 資料: {db_path}")
    
    try:
        shutil.rmtree(db_path)
        print("✅ 清理完成")
    except Exception as e:
        print(f"❌ 清理失敗: {e}")


def backup(db_root, backup_path):
    """備份 ChromaDB 資料"""
    db_path = Path(db_root) / '.chromadb'
    
    if not db_path.exists():
        print("⚠️  ChromaDB 資料不存在")
        return
    
    import shutil
    import datetime
    
    if not backup_path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"chromadb_backup_{timestamp}.tar.gz"
    
    print(f"📦 備份 ChromaDB 資料到: {backup_path}")
    
    try:
        import tarfile
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(db_path, arcname='.chromadb')
        
        print("✅ 備份完成")
        
        # 顯示備份大小
        import os
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"   大小: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")


def restore(db_root, backup_path):
    """恢復 ChromaDB 資料"""
    if not Path(backup_path).exists():
        print(f"❌ 備份檔案不存在: {backup_path}")
        return
    
    db_path = Path(db_root) / '.chromadb'
    
    print(f"📥 從備份恢復: {backup_path}")
    
    # 先清理現有資料
    if db_path.exists():
        import shutil
        shutil.rmtree(db_path)
    
    try:
        import tarfile
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=db_root)
        
        print("✅ 恢復完成")
        
    except Exception as e:
        print(f"❌ 恢復失敗: {e}")


def main():
    parser = argparse.ArgumentParser(description="ChromaDB 管理工具")
    parser.add_argument(
        "--db-root",
        type=str,
        default="PosTest",
        help="資料庫根目錄"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # stats 命令
    subparsers.add_parser('stats', help='顯示統計資訊')
    
    # rebuild 命令
    subparsers.add_parser('rebuild', help='重建索引')
    
    # clean 命令
    subparsers.add_parser('clean', help='清理資料')
    
    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='備份資料')
    backup_parser.add_argument('--output', type=str, help='備份檔案路徑')
    
    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='恢復資料')
    restore_parser.add_argument('backup_file', type=str, help='備份檔案路徑')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'stats':
        show_stats(args.db_root)
    elif args.command == 'rebuild':
        rebuild(args.db_root)
    elif args.command == 'clean':
        clean(args.db_root)
    elif args.command == 'backup':
        backup(args.db_root, args.output)
    elif args.command == 'restore':
        restore(args.db_root, args.backup_file)


if __name__ == "__main__":
    main()
