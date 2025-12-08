#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Few-shot 同步工具
用於在 questions.json 和 managed_examples.json 之間同步數據

使用方法:
    python sync_fewshot.py import   # 從 questions.json 導入到 managed_examples.json
    python sync_fewshot.py export   # 從 managed_examples.json 導出到 questions.json
    python sync_fewshot.py status   # 查看兩個檔案的狀態
"""

import json
import sys
from pathlib import Path
from datetime import datetime


class FewShotSync:
    def __init__(self, db_root_path="PosTest"):
        self.db_root_path = db_root_path
        self.questions_file = Path(db_root_path) / "fewshot" / "questions.json"
        self.managed_file = Path(db_root_path) / "fewshot" / "managed_examples.json"
        
    def load_questions_json(self):
        """載入 questions.json"""
        if not self.questions_file.exists():
            return {"extract": {}, "parse": {}, "questions": []}
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_managed_json(self):
        """載入 managed_examples.json"""
        if not self.managed_file.exists():
            return []
        with open(self.managed_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_questions_json(self, data):
        """保存 questions.json"""
        # 備份原檔案
        if self.questions_file.exists():
            backup_file = self.questions_file.with_suffix('.json.backup')
            import shutil
            shutil.copy2(self.questions_file, backup_file)
            print(f"✅ 已備份原檔案到: {backup_file}")
        
        with open(self.questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_managed_json(self, data):
        """保存 managed_examples.json"""
        with open(self.managed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def import_from_questions(self):
        """從 questions.json 導入到 managed_examples.json"""
        print("=" * 60)
        print("📥 從 questions.json 導入到 managed_examples.json")
        print("=" * 60)
        
        questions_data = self.load_questions_json()
        managed_data = self.load_managed_json()
        
        # 獲取現有的 question_id
        existing_ids = {item['question_id'] for item in managed_data}
        
        imported_count = 0
        skipped_count = 0
        
        # 從 questions 列表導入
        for item in questions_data.get("questions", []):
            # 嘗試從 prompt 中提取 SQL
            sql = ""
            if "prompt" in item:
                lines = item["prompt"].split('\n')
                # 找到 SQL 部分（通常在最後）
                sql_lines = []
                in_sql = False
                for line in lines:
                    if line.startswith("SELECT") or line.startswith("INSERT") or \
                       line.startswith("UPDATE") or line.startswith("DELETE"):
                        in_sql = True
                    if in_sql:
                        sql_lines.append(line)
                sql = '\n'.join(sql_lines).strip()
            
            # 生成 question_id（使用列表索引）
            question_id = questions_data["questions"].index(item)
            
            if question_id in existing_ids:
                print(f"⏭️  跳過已存在的範例 ID: {question_id}")
                skipped_count += 1
                continue
            
            new_item = {
                "question_id": question_id,
                "db_id": item.get("db_id", "PosTest"),
                "question": item.get("question", ""),
                "raw_question": item.get("question", ""),
                "evidence": item.get("evidence", ""),
                "SQL": sql,
                "difficulty": "simple"  # 預設難度
            }
            
            managed_data.append(new_item)
            imported_count += 1
            print(f"✅ 導入: {new_item['question']}")
        
        # 保存
        self.save_managed_json(managed_data)
        
        print("\n" + "=" * 60)
        print(f"📊 導入完成！")
        print(f"   新增: {imported_count} 個範例")
        print(f"   跳過: {skipped_count} 個範例")
        print(f"   總計: {len(managed_data)} 個範例")
        print("=" * 60)
    
    def export_to_questions(self):
        """從 managed_examples.json 導出到 questions.json"""
        print("=" * 60)
        print("📤 從 managed_examples.json 導出到 questions.json")
        print("=" * 60)
        
        managed_data = self.load_managed_json()
        questions_data = self.load_questions_json()
        
        if not managed_data:
            print("❌ managed_examples.json 是空的，無法導出")
            return
        
        # 重建 questions.json 結構
        new_questions_data = {
            "extract": {},
            "parse": {},
            "questions": []
        }
        
        for item in managed_data:
            qid = item['question_id']  # Keep as integer
            question = item['question']
            sql = item['SQL']
            evidence = item.get('evidence', '')
            
            # 生成 extract prompt
            extract_prompt = self._generate_extract_prompt(question, sql, evidence)
            new_questions_data["extract"][qid] = {"prompt": extract_prompt}
            
            # 生成 parse prompt
            parse_prompt = self._generate_parse_prompt(question, sql)
            new_questions_data["parse"][qid] = {"prompt": parse_prompt}
            
            # 生成完整 question
            full_prompt = self._generate_full_prompt(question, sql, item.get('db_id', 'PosTest'))
            new_questions_data["questions"].append({
                "question": question,
                "db_id": item.get('db_id', 'PosTest'),
                "prompt": full_prompt
            })
        
        # 保存
        self.save_questions_json(new_questions_data)
        
        print("\n" + "=" * 60)
        print(f"📊 導出完成！")
        print(f"   導出: {len(managed_data)} 個範例")
        print(f"   檔案: {self.questions_file}")
        print("=" * 60)
        print("\n⚠️  注意：")
        print("   1. 原 questions.json 已備份")
        print("   2. 請檢查生成的 prompt 格式是否正確")
        print("   3. 建議先測試再正式使用")
    
    def _generate_extract_prompt(self, question, sql, evidence):
        """生成 extract prompt"""
        # 從 SQL 提取關鍵資訊
        columns = self._extract_columns_from_sql(sql)
        values = self._extract_values_from_sql(sql)
        
        prompt = f"""/* 範例：提取問題中的關鍵資訊 */
/* 問題：{question} */
/* 提示：{evidence if evidence else 'None'} */
#reason: 這個問題需要查詢相關的資料表和欄位
#key_columns: {', '.join(columns) if columns else 'None'}
#key_values: {', '.join(values) if values else 'None'}
#answer: {sql}"""
        return prompt
    
    def _generate_parse_prompt(self, question, sql):
        """生成 parse prompt"""
        columns = self._extract_columns_from_sql(sql)
        operations = self._extract_operations_from_sql(sql)
        
        prompt = f"""/* 範例：解析問題中的欄位和值 */
/* 問題：{question} */
#columns: {', '.join(columns) if columns else 'None'}
#values: None
#operations: {', '.join(operations) if operations else 'SELECT'}"""
        return prompt
    
    def _generate_full_prompt(self, question, sql, db_id):
        """生成完整 prompt（包含 schema）"""
        # 這裡簡化處理，實際應該從資料庫讀取 schema
        prompt = f"""/* 給定以下資料庫 schema: */
/* 請根據實際資料庫補充 schema */

/* 回答以下問題：{question} */
{sql}"""
        return prompt
    
    def _extract_columns_from_sql(self, sql):
        """從 SQL 提取欄位名稱（簡化版）"""
        import re
        # 簡單的正則提取，實際可能需要更複雜的解析
        columns = re.findall(r'(\w+\.\w+)', sql)
        return list(set(columns))[:5]  # 最多返回 5 個
    
    def _extract_values_from_sql(self, sql):
        """從 SQL 提取值（簡化版）"""
        import re
        values = re.findall(r"'([^']+)'", sql)
        return list(set(values))[:3]  # 最多返回 3 個
    
    def _extract_operations_from_sql(self, sql):
        """從 SQL 提取操作"""
        operations = []
        sql_upper = sql.upper()
        
        if 'COUNT' in sql_upper:
            operations.append('COUNT')
        if 'SUM' in sql_upper:
            operations.append('SUM')
        if 'AVG' in sql_upper:
            operations.append('AVG')
        if 'JOIN' in sql_upper:
            operations.append('JOIN')
        if 'GROUP BY' in sql_upper:
            operations.append('GROUP BY')
        if 'ORDER BY' in sql_upper:
            operations.append('ORDER BY')
        if 'LIMIT' in sql_upper:
            operations.append('LIMIT')
        
        return operations if operations else ['SELECT']
    
    def show_status(self):
        """顯示兩個檔案的狀態"""
        print("=" * 60)
        print("📊 Few-shot 檔案狀態")
        print("=" * 60)
        
        # questions.json 狀態
        questions_data = self.load_questions_json()
        extract_count = len(questions_data.get("extract", {}))
        parse_count = len(questions_data.get("parse", {}))
        questions_count = len(questions_data.get("questions", []))
        
        print(f"\n📄 questions.json (系統使用)")
        print(f"   路徑: {self.questions_file}")
        print(f"   Extract 範例: {extract_count}")
        print(f"   Parse 範例: {parse_count}")
        print(f"   Questions 範例: {questions_count}")
        
        if questions_count > 0:
            print(f"\n   範例列表:")
            for i, q in enumerate(questions_data.get("questions", [])):
                print(f"   {i}. {q.get('question', 'N/A')}")
        
        # managed_examples.json 狀態
        managed_data = self.load_managed_json()
        
        print(f"\n📄 managed_examples.json (Web 界面)")
        print(f"   路徑: {self.managed_file}")
        print(f"   範例數量: {len(managed_data)}")
        
        if managed_data:
            print(f"\n   範例列表:")
            for item in managed_data:
                print(f"   {item['question_id']}. {item['question']}")
        
        print("\n" + "=" * 60)
        
        # 給出建議
        if questions_count > len(managed_data):
            print("💡 建議: 執行 'import' 將 questions.json 的範例導入到 Web 界面")
        elif len(managed_data) > questions_count:
            print("💡 建議: 執行 'export' 將 Web 界面的範例導出到 questions.json")
        else:
            print("✅ 兩個檔案的範例數量一致")
        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python sync_fewshot.py import [DB_NAME]   # 從 questions.json 導入")
        print("  python sync_fewshot.py export [DB_NAME]   # 導出到 questions.json")
        print("  python sync_fewshot.py status [DB_NAME]   # 查看狀態")
        print("")
        print("DB_NAME 預設為 PosTest")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    db_name = sys.argv[2] if len(sys.argv) > 2 else "PosTest"
    
    sync = FewShotSync(db_root_path=db_name)
    
    if command == "import":
        sync.import_from_questions()
    elif command == "export":
        sync.export_to_questions()
    elif command == "status":
        sync.show_status()
    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: import, export, status")
        print("使用方法:")
        print("  python sync_fewshot.py <command> [DB_NAME]")
        sys.exit(1)


if __name__ == "__main__":
    main()
