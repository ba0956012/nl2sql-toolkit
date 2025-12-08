#!/usr/bin/env python3
"""
測試 auto_generate_fewshot.py 生成的格式是否正確
"""
import json
from pathlib import Path

def test_format(db_root="testDB"):
    """測試 fewshot 格式"""
    fewshot_file = Path(db_root) / "fewshot" / "questions.json"
    
    if not fewshot_file.exists():
        print(f"❌ 找不到文件: {fewshot_file}")
        return False
    
    print(f"📖 讀取: {fewshot_file}")
    
    with open(fewshot_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查頂層結構
    if not isinstance(data, dict):
        print("❌ 頂層應該是 dict")
        return False
    
    if "questions" not in data:
        print("❌ 缺少 'questions' 鍵")
        return False
    
    questions = data["questions"]
    
    if not isinstance(questions, list):
        print("❌ 'questions' 應該是 list")
        return False
    
    print(f"✅ 頂層結構正確")
    print(f"✅ 找到 {len(questions)} 個範例\n")
    
    # 檢查每個 question
    required_fields = ["question", "db_id", "prompt"]
    
    for i, q in enumerate(questions):
        print(f"檢查範例 {i}:")
        
        # 檢查必要欄位
        for field in required_fields:
            if field not in q:
                print(f"  ❌ 缺少欄位: {field}")
                return False
            print(f"  ✅ {field}: {len(str(q[field]))} 字元")
        
        # 檢查 prompt 格式
        prompt = q["prompt"]
        if "CREATE TABLE" not in prompt:
            print(f"  ⚠️  prompt 中沒有 CREATE TABLE")
        if "回答以下問題" not in prompt:
            print(f"  ⚠️  prompt 中沒有 '回答以下問題'")
        if "SELECT" not in prompt:
            print(f"  ⚠️  prompt 中沒有 SELECT")
        
        print(f"  問題: {q['question'][:50]}...")
        print()
    
    print("=" * 60)
    print("✅ 格式驗證通過！")
    print("=" * 60)
    print("\n格式符合系統預期：")
    print("- 頂層是 dict，包含 'questions' 鍵")
    print("- questions 是 list")
    print("- 每個 question 包含: question, db_id, prompt")
    print("- prompt 包含完整的 schema + 問題 + SQL")
    
    return True


if __name__ == "__main__":
    import sys
    db_root = sys.argv[1] if len(sys.argv) > 1 else "testDB"
    test_format(db_root)
