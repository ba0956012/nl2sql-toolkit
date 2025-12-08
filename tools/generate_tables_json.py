#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動生成 tables.json 文件
使用方法:
    python tools/generate_tables_json.py \
        --database MyDB/dev/dev_databases/MyDB/MyDB.sqlite \
        --db-id MyDB \
        --output MyDB/data_preprocess/tables.json
"""

import sqlite3
import json
import argparse

def generate_tables_json(db_path, db_id, output_path):
    """
    生成 tables.json 文件
    
    Args:
        db_path: SQLite 資料庫路徑
        db_id: 資料庫 ID
        output_path: 輸出文件路徑
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 獲取所有表（排除 SQLite 系統表）
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    table_names = [t[0] for t in tables]
    
    print(f"找到 {len(table_names)} 個表: {', '.join(table_names)}")
    
    # 初始化
    column_names = [[-1, "*"]]
    column_names_original = [[-1, "*"]]
    column_types = ["text"]
    primary_keys = []
    foreign_keys = []
    
    # 處理每個表
    for table_idx, table_name in enumerate(table_names):
        print(f"\n處理表 {table_idx}: {table_name}")
        
        # 獲取列信息
        columns = cursor.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
        
        for col in columns:
            col_id = col[0]
            col_name = col[1]
            col_type = col[2].upper()
            not_null = col[3]
            default_val = col[4]
            is_pk = col[5]
            
            # 添加列
            column_names.append([table_idx, col_name])
            column_names_original.append([table_idx, col_name])
            
            # 判斷類型
            if any(t in col_type for t in ['INT', 'REAL', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']):
                column_types.append('number')
            elif 'DATE' in col_type or 'TIME' in col_type:
                column_types.append('time')
            else:
                column_types.append('text')
            
            # 記錄主鍵
            if is_pk:
                pk_index = len(column_names) - 1
                primary_keys.append(pk_index)
                print(f"  主鍵: {col_name} (索引 {pk_index})")
        
        # 獲取外鍵
        fks = cursor.execute(f"PRAGMA foreign_key_list(`{table_name}`)").fetchall()
        for fk in fks:
            fk_id = fk[0]
            fk_seq = fk[1]
            ref_table = fk[2]
            from_col = fk[3]
            to_col = fk[4]
            
            # 找到列索引
            from_idx = None
            to_idx = None
            
            for idx, (t_idx, c_name) in enumerate(column_names[1:], 1):
                if t_idx == table_idx and c_name == from_col:
                    from_idx = idx
                if table_names[t_idx] == ref_table and c_name == to_col:
                    to_idx = idx
            
            if from_idx and to_idx:
                foreign_keys.append([from_idx, to_idx])
                print(f"  外鍵: {table_name}.{from_col} -> {ref_table}.{to_col} ({from_idx} -> {to_idx})")
    
    conn.close()
    
    # 構建 JSON
    tables_json = [{
        "db_id": db_id,
        "table_names_original": table_names,
        "table_names": table_names,
        "column_names_original": column_names_original,
        "column_names": column_names,
        "column_types": column_types,
        "foreign_keys": foreign_keys,
        "primary_keys": primary_keys
    }]
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_json, f, indent=4, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ 生成完成！")
    print(f"{'='*60}")
    print(f"輸出文件: {output_path}")
    print(f"表數量: {len(table_names)}")
    print(f"列數量: {len(column_names) - 1}")
    print(f"主鍵數量: {len(primary_keys)}")
    print(f"外鍵數量: {len(foreign_keys)}")
    
    if len(foreign_keys) == 0:
        print(f"\n⚠️  警告: 未檢測到外鍵關係")
        print(f"   如果表之間有關聯，請手動添加到 foreign_keys 中")
    
    return tables_json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成 tables.json 文件')
    parser.add_argument('--database', required=True, help='SQLite 資料庫路徑')
    parser.add_argument('--db-id', required=True, help='資料庫 ID')
    parser.add_argument('--output', required=True, help='輸出文件路徑')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  生成 tables.json 文件")
    print("=" * 60)
    print(f"資料庫: {args.database}")
    print(f"DB ID: {args.db_id}")
    print(f"輸出: {args.output}")
    print("=" * 60)
    
    generate_tables_json(args.database, args.db_id, args.output)
