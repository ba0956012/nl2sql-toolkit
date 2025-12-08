#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
驗證 few-shot 範例的 SQL 正確性
使用方法:
    python tools/validate_fewshot.py \
        --fewshot MyDB/fewshot/questions.json \
        --database MyDB/dev/dev_databases/MyDB/MyDB.sqlite
"""

import json
import sqlite3
import argparse

def validate_fewshot(fewshot_path, db_path):
    """
    驗證 few-shot 範例
    
    Args:
        fewshot_path: few-shot JSON 文件路徑
        db_path: SQLite 資料庫路徑
    """
    # 載入 few-shot
    with open(fewshot_path, 'r', encoding='utf-8') as f:
        examples = json.load(f)
    
    print(f"載入 {len(examples)} 個 few-shot 範例")
    
    # 連接資料庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 驗證每個範例
    errors = []
    warnings = []
    success_count = 0
    
    for i, example in enumerate(examples):
        question = example.get('question', '')
        sql = example.get('SQL', '')
        difficulty = example.get('difficulty', 'unknown')
        
        print(f"\n[{i+1}/{len(examples)}] {difficulty.upper()}")
        print(f"問題: {question}")
        print(f"SQL: {sql}")
        
        # 檢查必要字段
        if not question:
            warnings.append({
                'index': i,
                'type': 'missing_question',
                'message': '缺少問題'
            })
            print("  ⚠️  警告: 缺少問題")
        
        if not sql:
            errors.append({
                'index': i,
                'question': question,
                'type': 'missing_sql',
                'message': '缺少 SQL'
            })
            print("  ❌ 錯誤: 缺少 SQL")
            continue
        
        # 執行 SQL
        try:
            result = cursor.execute(sql).fetchall()
            print(f"  ✅ SQL 正確 (返回 {len(result)} 行)")
            success_count += 1
            
            # 檢查是否返回結果
            if len(result) == 0:
                warnings.append({
                    'index': i,
                    'question': question,
                    'sql': sql,
                    'type': 'empty_result',
                    'message': 'SQL 執行成功但返回空結果'
                })
                print("  ⚠️  警告: 返回空結果")
        
        except Exception as e:
            errors.append({
                'index': i,
                'question': question,
                'sql': sql,
                'type': 'sql_error',
                'error': str(e)
            })
            print(f"  ❌ SQL 錯誤: {e}")
    
    conn.close()
    
    # 統計
    print(f"\n{'='*60}")
    print(f"驗證完成")
    print(f"{'='*60}")
    print(f"總數: {len(examples)}")
    print(f"成功: {success_count} ✅")
    print(f"錯誤: {len(errors)} ❌")
    print(f"警告: {len(warnings)} ⚠️")
    
    # 難度分布
    difficulty_count = {}
    for ex in examples:
        diff = ex.get('difficulty', 'unknown')
        difficulty_count[diff] = difficulty_count.get(diff, 0) + 1
    
    print(f"\n難度分布:")
    for diff, count in sorted(difficulty_count.items()):
        percentage = count / len(examples) * 100
        print(f"  {diff}: {count} ({percentage:.1f}%)")
    
    # 詳細錯誤
    if errors:
        print(f"\n{'='*60}")
        print(f"錯誤詳情")
        print(f"{'='*60}")
        for err in errors:
            print(f"\n[{err['index']}] {err.get('question', 'N/A')}")
            print(f"SQL: {err.get('sql', 'N/A')}")
            print(f"錯誤: {err.get('error', err.get('message', 'Unknown'))}")
    
    # 警告
    if warnings:
        print(f"\n{'='*60}")
        print(f"警告詳情")
        print(f"{'='*60}")
        for warn in warnings:
            print(f"\n[{warn['index']}] {warn.get('question', 'N/A')}")
            print(f"警告: {warn['message']}")
    
    # 建議
    print(f"\n{'='*60}")
    print(f"建議")
    print(f"{'='*60}")
    
    if len(examples) < 10:
        print("⚠️  Few-shot 範例較少（< 10），建議增加到 15-30 個")
    
    simple_count = difficulty_count.get('simple', 0)
    moderate_count = difficulty_count.get('moderate', 0)
    challenging_count = difficulty_count.get('challenging', 0)
    
    if simple_count < len(examples) * 0.2:
        print("⚠️  簡單範例較少，建議增加基本查詢範例")
    
    if challenging_count < len(examples) * 0.1:
        print("⚠️  困難範例較少，建議增加複雜查詢範例")
    
    if errors:
        print("❌ 請修復所有 SQL 錯誤後再使用")
        return False
    else:
        print("✅ 所有 SQL 都正確，可以使用！")
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='驗證 few-shot 範例')
    parser.add_argument('--fewshot', required=True, help='few-shot JSON 文件路徑')
    parser.add_argument('--database', required=True, help='SQLite 資料庫路徑')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  驗證 Few-shot 範例")
    print("=" * 60)
    print(f"Few-shot: {args.fewshot}")
    print(f"資料庫: {args.database}")
    print("=" * 60)
    
    success = validate_fewshot(args.fewshot, args.database)
    
    exit(0 if success else 1)
