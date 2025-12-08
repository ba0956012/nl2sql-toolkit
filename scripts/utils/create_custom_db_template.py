#!/usr/bin/env python3
"""
建立自訂資料庫模板的輔助腳本
使用方式：python create_custom_db_template.py --db_name MyDB --db_path /path/to/your.sqlite
"""

import argparse
import json
import os
import sqlite3
from pathlib import Path


def get_sqlite_schema(db_path):
    """從 SQLite 資料庫提取 schema 資訊"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 獲取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema_info = {}
    for table in tables:
        # 獲取表的欄位資訊
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        # 獲取外鍵資訊
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        foreign_keys = cursor.fetchall()
        
        schema_info[table] = {
            'columns': columns,
            'foreign_keys': foreign_keys
        }
    
    conn.close()
    return tables, schema_info


def map_sqlite_type(sqlite_type):
    """將 SQLite 類型映射到專案需要的類型"""
    sqlite_type = sqlite_type.upper()
    if 'INT' in sqlite_type or 'REAL' in sqlite_type or 'DOUBLE' in sqlite_type or 'FLOAT' in sqlite_type or 'NUMERIC' in sqlite_type:
        return 'number'
    elif 'TEXT' in sqlite_type or 'CHAR' in sqlite_type or 'CLOB' in sqlite_type:
        return 'text'
    elif 'DATE' in sqlite_type or 'TIME' in sqlite_type:
        return 'time'
    elif 'BOOL' in sqlite_type:
        return 'boolean'
    else:
        return 'others'


def create_tables_json(db_id, tables, schema_info):
    """建立 tables.json 格式的資料"""
    table_names_original = tables
    table_names = tables  # 可以自訂更易讀的名稱
    
    column_names_original = [[-1, "*"]]
    column_names = [[-1, "*"]]
    column_types = ["text"]
    primary_keys = []
    foreign_keys = []
    
    column_index = 1
    table_column_map = {}  # 用於追蹤每個表的欄位索引
    
    for table_idx, table in enumerate(tables):
        table_column_map[table] = {}
        columns = schema_info[table]['columns']
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            
            # 記錄欄位索引
            table_column_map[table][col_name] = column_index
            
            # 添加欄位
            column_names_original.append([table_idx, col_name])
            column_names.append([table_idx, col_name])  # 可以自訂更易讀的名稱
            column_types.append(map_sqlite_type(col_type))
            
            # 記錄主鍵
            if is_pk:
                primary_keys.append(column_index)
            
            column_index += 1
    
    # 處理外鍵
    for table_idx, table in enumerate(tables):
        fks = schema_info[table]['foreign_keys']
        for fk in fks:
            fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
            
            # 找到外鍵欄位的索引
            from_idx = table_column_map[table].get(from_col)
            to_idx = table_column_map[ref_table].get(to_col)
            
            if from_idx and to_idx:
                foreign_keys.append([from_idx, to_idx])
    
    return {
        "db_id": db_id,
        "table_names_original": table_names_original,
        "table_names": table_names,
        "column_names_original": column_names_original,
        "column_names": column_names,
        "column_types": column_types,
        "foreign_keys": foreign_keys,
        "primary_keys": primary_keys
    }


def create_question_template(db_id):
    """建立問題模板"""
    return [
        {
            "question_id": 0,
            "db_id": db_id,
            "question": "請在這裡輸入你的自然語言問題",
            "evidence": "可以在這裡提供額外的提示或說明",
            "SQL": "SELECT * FROM table_name LIMIT 1",
            "difficulty": "simple"
        }
    ]


def main():
    parser = argparse.ArgumentParser(description='建立自訂資料庫模板')
    parser.add_argument('--db_name', type=str, required=True, help='資料庫專案名稱（例如：MyDB）')
    parser.add_argument('--db_path', type=str, required=True, help='SQLite 資料庫檔案路徑')
    parser.add_argument('--output_dir', type=str, default='.', help='輸出目錄（預設為當前目錄）')
    
    args = parser.parse_args()
    
    db_name = args.db_name
    db_path = args.db_path
    output_dir = Path(args.output_dir)
    
    # 檢查資料庫檔案是否存在
    if not os.path.exists(db_path):
        print(f"錯誤：找不到資料庫檔案 {db_path}")
        return
    
    print(f"正在分析資料庫：{db_path}")
    
    # 提取 schema
    tables, schema_info = get_sqlite_schema(db_path)
    print(f"找到 {len(tables)} 個表：{', '.join(tables)}")
    
    # 建立目錄結構
    base_dir = output_dir / db_name
    dev_dir = base_dir / "dev"
    dev_db_dir = dev_dir / "dev_databases" / db_name
    train_dir = base_dir / "train"
    fewshot_dir = base_dir / "fewshot"
    
    for dir_path in [dev_dir, dev_db_dir, train_dir, fewshot_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n建立目錄結構於：{base_dir}")
    
    # 複製資料庫檔案
    import shutil
    target_db_path = dev_db_dir / f"{db_name}.sqlite"
    shutil.copy2(db_path, target_db_path)
    print(f"複製資料庫到：{target_db_path}")
    
    # 建立 tables.json
    tables_data = create_tables_json(db_name, tables, schema_info)
    
    dev_tables_path = dev_dir / "dev_tables.json"
    with open(dev_tables_path, 'w', encoding='utf-8') as f:
        json.dump([tables_data], f, indent=4, ensure_ascii=False)
    print(f"建立：{dev_tables_path}")
    
    train_tables_path = train_dir / "train_tables.json"
    with open(train_tables_path, 'w', encoding='utf-8') as f:
        json.dump([tables_data], f, indent=4, ensure_ascii=False)
    print(f"建立：{train_tables_path}")
    
    # 建立問題模板
    questions = create_question_template(db_name)
    
    dev_json_path = dev_dir / "dev.json"
    with open(dev_json_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
    print(f"建立：{dev_json_path}")
    
    train_json_path = train_dir / "train.json"
    with open(train_json_path, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=4, ensure_ascii=False)
    print(f"建立：{train_json_path}")
    
    # 建立 dev/db_schema.json 文件（避免被誤創建為目錄）
    dev_db_schema_path = dev_dir / "db_schema.json"
    with open(dev_db_schema_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)
    print(f"建立：{dev_db_schema_path}")
    
    # 建立空的 fewshot 檔案
    fewshot_path = fewshot_dir / "questions.json"
    with open(fewshot_path, 'w', encoding='utf-8') as f:
        json.dump({"extract": {}, "parse": {}, "questions": []}, f, indent=4, ensure_ascii=False)
    print(f"建立：{fewshot_path}")
    
    fewshot2_path = base_dir / "correct_fewshot2.json"
    with open(fewshot2_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)
    print(f"建立：{fewshot2_path}")
    
    # 建立空的 db_schema.json 文件（避免被誤創建為目錄）
    db_schema_path = base_dir / "db_schema.json"
    with open(db_schema_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)
    print(f"建立：{db_schema_path}")
    
    print(f"\n✅ 模板建立完成！")
    print(f"\n下一步：")
    print(f"1. 編輯 {dev_json_path} 添加你的問題")
    print(f"2. 檢查 {dev_tables_path} 確認 schema 正確")
    print(f"3. 執行預處理：sh run/run_preprocess.sh（記得修改 db_root_directory={db_name}）")
    print(f"4. 執行主程式：sh run/run_main.sh（記得修改 db_root_path={db_name}）")
    
    # 顯示資料庫 schema 摘要
    print(f"\n資料庫 Schema 摘要：")
    for table in tables:
        columns = schema_info[table]['columns']
        print(f"\n表：{table}")
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            pk_mark = " [PK]" if is_pk else ""
            print(f"  - {col_name} ({col_type}){pk_mark}")


if __name__ == "__main__":
    main()
