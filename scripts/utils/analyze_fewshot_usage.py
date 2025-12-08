#!/usr/bin/env python3
"""
分析日誌中使用的 Few-shot 範例
"""

import re
import json
from pathlib import Path
from collections import Counter
import argparse


def analyze_log_file(log_file):
    """分析單個日誌檔案"""
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜尋 few-shot 使用記錄
    extract_pattern = r'Using extract few-shot example #(\d+)'
    candidate_pattern = r'Using few-shot example #(\d+): (.+?)\.{3}'
    
    extract_matches = re.findall(extract_pattern, content)
    candidate_matches = re.findall(candidate_pattern, content)
    
    return {
        'extract_examples': extract_matches,
        'candidate_examples': [(m[0], m[1]) for m in candidate_matches]
    }


def analyze_logs_directory(logs_dir, db_root):
    """分析整個日誌目錄"""
    logs_path = Path(logs_dir)
    
    if not logs_path.exists():
        print(f"❌ 日誌目錄不存在: {logs_dir}")
        return
    
    log_files = list(logs_path.glob("*.log"))
    
    if not log_files:
        print(f"⚠️  沒有找到日誌檔案在: {logs_dir}")
        return
    
    print(f"📊 分析 {len(log_files)} 個日誌檔案...")
    print()
    
    all_extract_examples = []
    all_candidate_examples = []
    
    for log_file in log_files:
        result = analyze_log_file(log_file)
        all_extract_examples.extend(result['extract_examples'])
        all_candidate_examples.extend(result['candidate_examples'])
    
    # 統計使用頻率
    extract_counter = Counter(all_extract_examples)
    candidate_counter = Counter([ex[0] for ex in all_candidate_examples])
    
    print("=" * 60)
    print("📈 Few-shot 使用統計")
    print("=" * 60)
    print()
    
    print("🔍 Extract Few-shot 使用次數:")
    if extract_counter:
        for example_id, count in extract_counter.most_common():
            print(f"  範例 #{example_id}: {count} 次")
    else:
        print("  (無記錄)")
    
    print()
    print("🎯 Candidate Few-shot 使用次數:")
    if candidate_counter:
        for example_id, count in candidate_counter.most_common():
            # 找到對應的問題
            questions = [ex[1] for ex in all_candidate_examples if ex[0] == example_id]
            question = questions[0] if questions else "N/A"
            print(f"  範例 #{example_id}: {count} 次")
            print(f"    問題: {question[:80]}...")
    else:
        print("  (無記錄)")
    
    print()
    print("=" * 60)
    
    # 載入 fewshot 檔案來顯示完整資訊
    fewshot_file = Path(db_root) / "fewshot" / "questions.json"
    if fewshot_file.exists():
        print()
        print("📚 Few-shot 範例詳情:")
        print("=" * 60)
        
        with open(fewshot_file, 'r', encoding='utf-8') as f:
            fewshot_data = json.load(f)
        
        # 顯示最常使用的範例
        print()
        print("🔥 最常使用的範例:")
        for example_id, count in candidate_counter.most_common(5):
            idx = int(example_id)
            if idx < len(fewshot_data.get('questions', [])):
                example = fewshot_data['questions'][idx]
                print(f"\n範例 #{example_id} (使用 {count} 次):")
                print(f"  問題: {example.get('question', 'N/A')}")
                if 'prompt' in example:
                    # 提取 SQL
                    prompt = example['prompt']
                    sql_match = re.search(r'SELECT.*?(?=\n\n|$)', prompt, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        print(f"  SQL: {sql[:100]}...")


def main():
    parser = argparse.ArgumentParser(description="分析 Few-shot 使用情況")
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs/logs",
        help="日誌目錄路徑"
    )
    parser.add_argument(
        "--db-root",
        type=str,
        default="PosTest",
        help="資料庫根目錄"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Few-shot 使用分析工具")
    print("=" * 60)
    print()
    
    analyze_logs_directory(args.logs_dir, args.db_root)
    
    print()
    print("💡 提示:")
    print("  - 如果某些範例從未被使用，可能需要改進")
    print("  - 如果某些範例使用頻率很高，表示它們很有代表性")
    print("  - 可以根據使用情況調整 Few-shot 範例")
    print()


if __name__ == "__main__":
    main()
