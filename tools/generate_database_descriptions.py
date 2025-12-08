#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動生成 database_description 文件
使用方法:
    python tools/generate_database_descriptions.py \
        --database MyDB/dev/dev_databases/MyDB/MyDB.sqlite \
        --output MyDB/dev/dev_databases/MyDB/database_description/
"""

import sqlite3
import pandas as pd
import os
import argparse

def generate_descriptions(db_path, output_dir, use_gpt=False):
    """
    生成 database_description 文件
    
    Args:
        db_path: SQLite 資料庫路徑
        output_dir: 輸出目錄
        use_gpt: 是否使用 GPT 生成更好的描述
    """
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 獲取所有表名
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    
    print(f"找到 {len(tables)} 個表")
    
    for table_name, in tables:
        print(f"\n處理表: {table_name}")
        
        # 獲取列信息
        columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        
        # 獲取樣本數據
        try:
            sample_data = cursor.execute(
                f"SELECT * FROM {table_name} LIMIT 3"
            ).fetchall()
        except:
            sample_data = []
        
        # 創建描述數據
        data = []
        for col in columns:
            col_id = col[0]
            col_name = col[1]
            col_type = col[2]
            not_null = col[3]
            default_val = col[4]
            is_pk = col[5]
            
            # 基本描述
            col_desc = f"{col_name} ({col_type})"
            if is_pk:
                col_desc += " - Primary Key"
            if not_null:
                col_desc += " - Not Null"
            
            # 值描述
            val_desc = f"Type: {col_type}"
            if sample_data and col_id < len(sample_data[0]):
                samples = [row[col_id] for row in sample_data if row[col_id] is not None]
                if samples:
                    val_desc += f" | Examples: {', '.join(map(str, samples[:3]))}"
            
            data.append({
                'column_name': col_name,
                'unused1': '',
                'column_description': col_desc,
                'unused2': '',
                'value_description': val_desc
            })
        
        # 保存為 CSV
        df = pd.DataFrame(data)
        output_path = os.path.join(output_dir, f'{table_name}.csv')
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"  ✅ 創建 {table_name}.csv ({len(data)} 列)")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ 完成！生成了 {len(tables)} 個描述文件")
    print(f"{'='*60}")
    print(f"\n⚠️  重要提示:")
    print(f"   請手動編輯生成的 CSV 文件，添加更詳細的描述！")
    print(f"   特別是 column_description 和 value_description 欄位。")
    print(f"\n   輸出目錄: {output_dir}")

def generate_with_gpt(db_path, output_dir):
    """使用 GPT 生成更好的描述"""
    try:
        import sys
        sys.path.insert(0, '.')
        from azure_openai_config import get_azure_openai_client
        
        client = get_azure_openai_client()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        
        for table_name, in tables:
            print(f"\n使用 GPT 處理表: {table_name}")
            
            # 獲取表結構
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            sample_data = cursor.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
            
            # 構建 prompt
            schema_info = f"表名: {table_name}\n\n列:\n"
            for col in columns:
                schema_info += f"- {col[1]} ({col[2]})\n"
            
            schema_info += f"\n樣本數據:\n"
            for row in sample_data[:3]:
                schema_info += f"{row}\n"
            
            prompt = f"""
請為以下資料庫表生成詳細的列描述。

{schema_info}

請為每一列提供:
1. column_description: 列的業務含義和用途
2. value_description: 值的含義、格式、範圍等

以 JSON 格式返回:
[
    {{
        "column_name": "列名",
        "column_description": "詳細描述",
        "value_description": "值的描述"
    }},
    ...
]
"""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一個資料庫專家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            descriptions = json.loads(response.choices[0].message.content)
            
            # 保存
            data = []
            for desc in descriptions:
                data.append({
                    'column_name': desc['column_name'],
                    'unused1': '',
                    'column_description': desc['column_description'],
                    'unused2': '',
                    'value_description': desc['value_description']
                })
            
            df = pd.DataFrame(data)
            output_path = os.path.join(output_dir, f'{table_name}.csv')
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"  ✅ 創建 {table_name}.csv")
        
        conn.close()
        print(f"\n✅ 使用 GPT 生成完成！")
        
    except Exception as e:
        print(f"\n❌ GPT 生成失敗: {e}")
        print("   將使用基本方法生成...")
        generate_descriptions(db_path, output_dir, use_gpt=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成 database_description 文件')
    parser.add_argument('--database', required=True, help='SQLite 資料庫路徑')
    parser.add_argument('--output', required=True, help='輸出目錄')
    parser.add_argument('--use-gpt', action='store_true', help='使用 GPT 生成更好的描述')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  生成 Database Description 文件")
    print("=" * 60)
    print(f"資料庫: {args.database}")
    print(f"輸出: {args.output}")
    print(f"使用 GPT: {'是' if args.use_gpt else '否'}")
    print("=" * 60)
    
    if args.use_gpt:
        generate_with_gpt(args.database, args.output)
    else:
        generate_descriptions(args.database, args.output)
