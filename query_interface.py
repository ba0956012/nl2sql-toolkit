#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡單的問答接口 - 輸入自然語言問題，返回 SQL 查詢
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, "src")

from runner.run_manager import RunManager
import argparse


class QueryInterface:
    def __init__(self, db_root_path=None, data_mode="dev"):
        """
        初始化查詢接口

        Args:
            db_root_path: 資料庫根目錄（如果為 None，從環境變數 DB_ROOT_DIRECTORY 讀取，預設為 PosTest）
            data_mode: 資料模式 ('dev' 或 'train')
        """
        import os
        if db_root_path is None:
            db_root_path = os.getenv('DB_ROOT_DIRECTORY', 'PosTest')
        
        self.db_root_path = db_root_path
        self.data_mode = data_mode
        self.temp_json_path = Path(db_root_path) / "data_preprocess" / "temp_query.json"

    def create_temp_query(self, question, question_id=None):
        """
        創建臨時查詢 JSON 文件

        Args:
            question: 自然語言問題
            question_id: 問題 ID（如果為 None，則自動檢索最佳 few-shot）
        """
        # 如果沒有指定 question_id，使用 few-shot 檢索
        if question_id is None:
            try:
                # 優先使用 ChromaDB（更快）
                try:
                    from runner.fewshot_retriever_chroma import get_retriever

                    logging.info("Using ChromaDB for few-shot retrieval")
                except ImportError:
                    from runner.fewshot_retriever import get_retriever

                    logging.info("Using standard retrieval (ChromaDB not available)")

                fewshot_path = Path(self.db_root_path) / "fewshot" / "questions.json"
                retriever = get_retriever(str(fewshot_path))
                question_id = retriever.get_best_question_id(question)
                print(f"🎯 自動選擇 few-shot 範例 #{question_id}")
            except Exception as e:
                print(f"⚠️  Few-shot 檢索失敗，使用預設值: {e}")
                logging.error(f"Few-shot retrieval error: {e}")
                question_id = 0
        else:
            print(f"📌 使用指定的 few-shot 範例 #{question_id}")
        # 讀取原始資料以獲取資料庫結構
        original_json = (
            Path(self.db_root_path) / "data_preprocess" / f"{self.data_mode}.json"
        )
        with open(original_json, "r", encoding="utf-8") as f:
            original_data = json.load(f)

        # 使用第一個問題作為模板
        template = original_data[0].copy()

        # 更新問題內容
        template["question_id"] = question_id
        template["question"] = question
        template["raw_question"] = question
        template["evidence"] = ""
        template["SQL"] = ""  # 未知的 SQL

        # 創建臨時文件
        temp_data = [template]
        with open(self.temp_json_path, "w", encoding="utf-8") as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=2)

        return self.temp_json_path

    def query(self, question):
        """
        執行查詢

        Args:
            question: 自然語言問題

        Returns:
            生成的 SQL 查詢
        """
        print(f"\n🔍 處理問題: {question}")
        print("=" * 60)

        # 創建臨時查詢文件
        temp_file = self.create_temp_query(question)

        # 設置參數
        args = argparse.Namespace(
            data_mode=self.data_mode,
            db_root_path=self.db_root_path,
            pipeline_nodes="generate_db_schema+extract_col_value+extract_query_noun+column_retrieve_and_other_info+candidate_generate+align_correct+vote",
            pipeline_setup=json.dumps(
                {
                    "generate_db_schema": {
                        "engine": "gpt-4o-0513",
                        "bert_model": "all-MiniLM-L6-v2",
                        "device": "cpu",
                    },
                    "extract_col_value": {"engine": "gpt-4o-0513", "temperature": 0.0},
                    "extract_query_noun": {"engine": "gpt-4o-0513", "temperature": 0.0},
                    "column_retrieve_and_other_info": {
                        "engine": "gpt-4o-0513",
                        "bert_model": "all-MiniLM-L6-v2",
                        "device": "cpu",
                        "temperature": 0.3,
                        "top_k": 10,
                    },
                    "candidate_generate": {
                        "engine": "gpt-4o-0513",
                        "temperature": 0.7,
                        "n": 3,
                        "return_question": "True",
                        "single": "False",
                    },
                    "align_correct": {
                        "engine": "gpt-4o-0513",
                        "n": 3,
                        "bert_model": "all-MiniLM-L6-v2",
                        "device": "cpu",
                        "align_methods": "style_align+function_align+agent_align",
                    },
                }
            ),
            use_checkpoint=False,
            checkpoint_nodes=None,
            checkpoint_dir=None,
            log_level="warning",
            start=0,
            end=1,
            run_start_time=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        )

        # 載入資料集
        with open(temp_file, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        # 執行查詢
        run_manager = RunManager(args)
        run_manager.initialize_tasks(0, 1, dataset)
        run_manager.run_tasks()

        # 從結果文件中讀取 SQL
        results_base = Path("results") / self.data_mode

        if results_base.exists():
            # 找到最新的結果目錄
            db_results = list(results_base.glob(f"*/{self.db_root_path}/*"))

            if db_results:
                latest_result = max(db_results, key=lambda p: p.stat().st_mtime)

                # 嘗試找到任何 *_<db_name>.json 檔案
                result_files = list(latest_result.glob(f"*_{self.db_root_path}.json"))
                result_files = [f for f in result_files if not f.name.startswith("-")]

                if not result_files:
                    logging.warning(f"No result files found in: {latest_result}")
                    print("\n❌ 無法生成 SQL")
                    print("=" * 60)
                    return None

                # 使用最新的結果檔案
                result_file = max(result_files, key=lambda p: p.stat().st_mtime)

                logging.info(f"Looking for result file: {result_file}")

                if result_file.exists():
                    try:
                        with open(result_file, "r", encoding="utf-8") as f:
                            result_data = json.load(f)

                            # 結果是執行歷史列表，找到 vote 節點
                            if isinstance(result_data, list):
                                for node in reversed(result_data):
                                    if (
                                        node.get("node_type") == "vote"
                                        and "SQL" in node
                                        and node["SQL"]
                                    ):
                                        sql = node["SQL"]
                                        print(f"\n✅ 生成的 SQL:")
                                        print(f"   {sql}")
                                        print("=" * 60)
                                        return sql
                            # 如果是字典格式
                            elif (
                                isinstance(result_data, dict)
                                and "SQL" in result_data
                                and result_data["SQL"]
                            ):
                                sql = result_data["SQL"]
                                print(f"\n✅ 生成的 SQL:")
                                print(f"   {sql}")
                                print("=" * 60)
                                return sql
                    except Exception as e:
                        logging.error(f"Error reading result file: {e}")
                        import traceback

                        traceback.print_exc()
                else:
                    logging.warning(f"Result file not found: {result_file}")
            else:
                logging.warning(f"No result directories found in: {results_base}")
        else:
            logging.warning(f"Results base directory not found: {results_base}")

        print("\n❌ 無法生成 SQL")
        print("=" * 60)
        return None

    def cleanup(self):
        """清理臨時文件"""
        if self.temp_json_path.exists():
            self.temp_json_path.unlink()


def interactive_mode():
    """交互式模式"""
    print("=" * 60)
    print("🤖 OpenSearch-SQL 查詢接口")
    print("=" * 60)
    print("輸入自然語言問題，系統將生成對應的 SQL 查詢")
    print("輸入 'exit' 或 'quit' 退出")
    print("=" * 60)

    interface = QueryInterface()

    try:
        while True:
            question = input("\n💬 請輸入問題: ").strip()

            if question.lower() in ["exit", "quit", "退出"]:
                print("\n👋 再見！")
                break

            if not question:
                print("⚠️  請輸入有效的問題")
                continue

            try:
                sql = interface.query(question)
                if sql:
                    print(f"\n📋 可以直接執行的 SQL:")
                    print(f"   {sql}\n")
            except Exception as e:
                print(f"\n❌ 錯誤: {e}")
                import traceback

                traceback.print_exc()

    finally:
        interface.cleanup()


def single_query_mode(question):
    """單次查詢模式"""
    interface = QueryInterface()
    try:
        sql = interface.query(question)
        return sql
    finally:
        interface.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式：python query_interface.py "你的問題"
        question = " ".join(sys.argv[1:])
        sql = single_query_mode(question)
        if sql:
            print(sql)
    else:
        # 交互式模式
        interactive_mode()
