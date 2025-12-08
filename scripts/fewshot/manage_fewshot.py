#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Few-shot 管理工具 - CRUD 操作
使用方法:
    python manage_fewshot.py list                           # 列出所有範例
    python manage_fewshot.py add                            # 添加新範例（交互式）
    python manage_fewshot.py update <id>                    # 更新範例
    python manage_fewshot.py delete <id>                    # 刪除範例
    python manage_fewshot.py search <keyword>               # 搜尋範例
    python manage_fewshot.py validate                       # 驗證所有範例
"""

import json
import sys
import sqlite3
from pathlib import Path
import argparse


class FewShotManager:
    def __init__(self, db_root_path="PosTest"):
        self.db_root_path = db_root_path
        # 使用獨立的 few-shot 管理文件，不影響原有的 questions.json
        self.fewshot_file = Path(db_root_path) / "fewshot" / "managed_examples.json"
        self.db_path = (
            Path(db_root_path)
            / "dev"
            / "dev_databases"
            / db_root_path
            / f"{db_root_path}.sqlite"
        )

        # 如果文件不存在，創建空列表
        if not self.fewshot_file.exists():
            self.fewshot_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fewshot_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            print(f"✅ 創建新的 few-shot 管理文件: {self.fewshot_file}")
            print(f"   原有的 questions.json 保持不變")

    def load_fewshot(self):
        """載入 few-shot 資料"""
        if not self.fewshot_file.exists():
            return []
        with open(self.fewshot_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_fewshot(self, data):
        """保存 few-shot 資料"""
        with open(self.fewshot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def list_all(self):
        """列出所有範例"""
        data = self.load_fewshot()

        if not data:
            print("📭 沒有 few-shot 範例")
            return

        print(f"\n📚 Few-shot 範例列表 (共 {len(data)} 個)")
        print("=" * 80)

        for item in data:
            qid = item.get("question_id", "N/A")
            question = item.get("question", "N/A")
            sql = item.get("SQL", "N/A")
            difficulty = item.get("difficulty", "N/A")

            print(f"\n[{qid}] {difficulty.upper()}")
            print(f"問題: {question}")
            print(f"SQL:  {sql[:80]}{'...' if len(sql) > 80 else ''}")

        print("\n" + "=" * 80)

        # 統計
        difficulties = {}
        for item in data:
            diff = item.get("difficulty", "unknown")
            difficulties[diff] = difficulties.get(diff, 0) + 1

        print("\n📊 難度分布:")
        for diff, count in sorted(difficulties.items()):
            percentage = count / len(data) * 100
            print(f"  {diff}: {count} ({percentage:.1f}%)")

    def add_example(self, question=None, sql=None, difficulty=None, evidence=None):
        """添加新範例"""
        data = self.load_fewshot()

        # 獲取新的 ID
        new_id = max([item.get("question_id", 0) for item in data], default=-1) + 1

        # 交互式輸入
        if question is None:
            print("\n➕ 添加新的 Few-shot 範例")
            print("=" * 60)
            question = input("問題: ").strip()

        if sql is None:
            sql = input("SQL: ").strip()

        if difficulty is None:
            print("\n難度選擇:")
            print("  1. simple")
            print("  2. moderate")
            print("  3. challenging")
            choice = input("選擇 (1-3): ").strip()
            difficulty_map = {"1": "simple", "2": "moderate", "3": "challenging"}
            difficulty = difficulty_map.get(choice, "moderate")

        if evidence is None:
            evidence = input("提示 (可選): ").strip()

        # 驗證 SQL
        if self.validate_sql(sql):
            print("✅ SQL 驗證通過")
        else:
            confirm = input("⚠️  SQL 驗證失敗，是否仍要添加？(y/n): ")
            if confirm.lower() != "y":
                print("❌ 取消添加")
                return

        # 創建新範例
        new_example = {
            "question_id": new_id,
            "db_id": self.db_root_path,
            "question": question,
            "raw_question": question,
            "evidence": evidence,
            "SQL": sql,
            "difficulty": difficulty,
        }

        data.append(new_example)
        self.save_fewshot(data)

        print(f"\n✅ 成功添加範例 #{new_id}")
        print(f"   問題: {question}")
        print(f"   SQL: {sql}")
        print(f"   難度: {difficulty}")

    def update_example(self, question_id):
        """更新範例"""
        data = self.load_fewshot()

        # 找到範例
        example = None
        index = None
        for i, item in enumerate(data):
            if item.get("question_id") == question_id:
                example = item
                index = i
                break

        if example is None:
            print(f"❌ 找不到 ID 為 {question_id} 的範例")
            return

        print(f"\n✏️  更新範例 #{question_id}")
        print("=" * 60)
        print(f"當前問題: {example['question']}")
        print(f"當前 SQL: {example['SQL']}")
        print(f"當前難度: {example['difficulty']}")
        print(f"當前提示: {example.get('evidence', '')}")
        print("\n留空表示不修改")
        print("=" * 60)

        # 更新欄位
        new_question = input(f"新問題 [{example['question']}]: ").strip()
        if new_question:
            example["question"] = new_question
            example["raw_question"] = new_question

        new_sql = input(f"新 SQL [{example['SQL'][:50]}...]: ").strip()
        if new_sql:
            if self.validate_sql(new_sql):
                print("✅ SQL 驗證通過")
                example["SQL"] = new_sql
            else:
                confirm = input("⚠️  SQL 驗證失敗，是否仍要更新？(y/n): ")
                if confirm.lower() == "y":
                    example["SQL"] = new_sql

        new_difficulty = input(
            f"新難度 (simple/moderate/challenging) [{example['difficulty']}]: "
        ).strip()
        if new_difficulty:
            example["difficulty"] = new_difficulty

        new_evidence = input(f"新提示 [{example.get('evidence', '')}]: ").strip()
        if new_evidence:
            example["evidence"] = new_evidence

        data[index] = example
        self.save_fewshot(data)

        print(f"\n✅ 成功更新範例 #{question_id}")

    def delete_example(self, question_id):
        """刪除範例"""
        data = self.load_fewshot()

        # 找到範例
        example = None
        for item in data:
            if item.get("question_id") == question_id:
                example = item
                break

        if example is None:
            print(f"❌ 找不到 ID 為 {question_id} 的範例")
            return

        print(f"\n🗑️  刪除範例 #{question_id}")
        print("=" * 60)
        print(f"問題: {example['question']}")
        print(f"SQL: {example['SQL']}")
        print("=" * 60)

        confirm = input("確定要刪除嗎？(y/n): ")
        if confirm.lower() != "y":
            print("❌ 取消刪除")
            return

        # 刪除
        data = [item for item in data if item.get("question_id") != question_id]
        self.save_fewshot(data)

        print(f"✅ 成功刪除範例 #{question_id}")

    def search_examples(self, keyword):
        """搜尋範例"""
        data = self.load_fewshot()

        results = []
        for item in data:
            if (
                keyword.lower() in item.get("question", "").lower()
                or keyword.lower() in item.get("SQL", "").lower()
                or keyword.lower() in item.get("evidence", "").lower()
            ):
                results.append(item)

        if not results:
            print(f"🔍 沒有找到包含 '{keyword}' 的範例")
            return

        print(f"\n🔍 搜尋結果: 找到 {len(results)} 個範例")
        print("=" * 80)

        for item in results:
            qid = item.get("question_id", "N/A")
            question = item.get("question", "N/A")
            sql = item.get("SQL", "N/A")
            difficulty = item.get("difficulty", "N/A")

            print(f"\n[{qid}] {difficulty.upper()}")
            print(f"問題: {question}")
            print(f"SQL:  {sql}")

    def validate_sql(self, sql):
        """驗證 SQL 是否正確"""
        if not self.db_path.exists():
            print(f"⚠️  資料庫文件不存在: {self.db_path}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.close()
            return True
        except Exception as e:
            print(f"❌ SQL 錯誤: {e}")
            return False

    def validate_all(self):
        """驗證所有範例"""
        data = self.load_fewshot()

        if not data:
            print("📭 沒有 few-shot 範例")
            return

        print(f"\n🔍 驗證 {len(data)} 個範例...")
        print("=" * 80)

        errors = []
        for item in data:
            qid = item.get("question_id", "N/A")
            sql = item.get("SQL", "")

            if self.validate_sql(sql):
                print(f"✅ [{qid}] {item.get('question', '')[:50]}")
            else:
                print(f"❌ [{qid}] {item.get('question', '')[:50]}")
                errors.append(item)

        print("\n" + "=" * 80)
        print(f"結果: {len(data) - len(errors)}/{len(data)} 通過")

        if errors:
            print(f"\n⚠️  {len(errors)} 個範例有錯誤:")
            for item in errors:
                print(f"  [{item.get('question_id')}] {item.get('question')}")

    def export_to_dev(self):
        """導出到 dev.json 格式（用於系統訓練）"""
        data = self.load_fewshot()

        if not data:
            print("📭 沒有 few-shot 範例可導出")
            return

        output_file = Path(self.db_root_path) / "dev" / "dev.json"

        print(f"\n📤 導出 {len(data)} 個範例到 {output_file}")

        # 確認
        if output_file.exists():
            confirm = input(f"⚠️  文件已存在，是否覆蓋？(y/n): ")
            if confirm.lower() != "y":
                print("❌ 取消導出")
                return

        # 保存
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"✅ 成功導出到 {output_file}")
        print(f"   現在可以運行預處理來使用這些範例")


def main():
    parser = argparse.ArgumentParser(description="Few-shot 管理工具")
    parser.add_argument(
        "action",
        choices=["list", "add", "update", "delete", "search", "validate", "export"],
        help="操作類型",
    )
    parser.add_argument("args", nargs="*", help="額外參數")
    parser.add_argument("--db", default="PosTest", help="資料庫名稱")

    args = parser.parse_args()

    manager = FewShotManager(args.db)

    if args.action == "list":
        manager.list_all()

    elif args.action == "add":
        manager.add_example()

    elif args.action == "update":
        if not args.args:
            print("❌ 請提供要更新的範例 ID")
            print("使用方法: python manage_fewshot.py update <id>")
            return
        try:
            qid = int(args.args[0])
            manager.update_example(qid)
        except ValueError:
            print("❌ ID 必須是數字")

    elif args.action == "delete":
        if not args.args:
            print("❌ 請提供要刪除的範例 ID")
            print("使用方法: python manage_fewshot.py delete <id>")
            return
        try:
            qid = int(args.args[0])
            manager.delete_example(qid)
        except ValueError:
            print("❌ ID 必須是數字")

    elif args.action == "search":
        if not args.args:
            print("❌ 請提供搜尋關鍵字")
            print("使用方法: python manage_fewshot.py search <keyword>")
            return
        keyword = " ".join(args.args)
        manager.search_examples(keyword)

    elif args.action == "validate":
        manager.validate_all()

    elif args.action == "export":
        manager.export_to_dev()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Few-shot 管理工具")
        print("=" * 60)
        print("⚠️  此工具使用獨立文件 'managed_examples.json'")
        print("   不會修改原有的 'questions.json'")
        print("=" * 60)
        print("使用方法:")
        print("  python manage_fewshot.py list              # 列出所有範例")
        print("  python manage_fewshot.py add               # 添加新範例")
        print("  python manage_fewshot.py update <id>       # 更新範例")
        print("  python manage_fewshot.py delete <id>       # 刪除範例")
        print("  python manage_fewshot.py search <keyword>  # 搜尋範例")
        print("  python manage_fewshot.py validate          # 驗證所有範例")
        print("  python manage_fewshot.py export            # 導出到 dev.json")
        print()
        print("選項:")
        print(
            "  --db <name>                                # 指定資料庫 (預設: PosTest)"
        )
        sys.exit(0)

    main()
