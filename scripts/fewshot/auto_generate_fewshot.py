#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Few-shot 自動生成（SQLite 版本）
=====================================================
符合你的規則：

1. 嚴格依 SQLite PRAGMA 外鍵列表，不推論、不猜測、不寫死 FK。
2. 只使用 PRAGMA 外鍵構建 JOIN 圖（無向圖）→ BFS → JOIN Route。
3. SELECT 一律：  t0.*, t1.*, t2.* ...
4. WHERE 子句：
   - 永遠使用 root table alias = t0
   - TEXT 欄位：LIKE '%value%'
   - 非 TEXT：= value
   - NULL 不加入 WHERE
5. SQL 先以 SQLite execute 驗證，錯誤即跳過。
6. 每張表產生 1 筆 few-shot。
7. 輸出格式與你原系統完全一致：
   { extract: {}, parse: {}, questions: [ ... ] }
"""

import sqlite3
import json
import os
import argparse
from pathlib import Path
import sys

# === 添加專案根目錄到路徑 ===
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from runner.logger import Logger
from llm.model import model_chose


# =====================================================
#  取得 SQLite Schema
# =====================================================
def analyze_database(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 所有 table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cur.fetchall()]

    schema = {}
    for t in tables:
        cur.execute(f"PRAGMA table_info('{t}');")
        cols = cur.fetchall()

        cur.execute(f"PRAGMA foreign_key_list('{t}');")
        fks = cur.fetchall()

        schema[t] = {
            "columns": cols,
            "fks": fks
        }

    conn.close()
    return tables, schema


# =====================================================
#  建 FK Graph（無向圖）
# =====================================================
def build_fk_graph(tables, schema):
    graph = {t: [] for t in tables}

    for t in tables:
        for fk in schema[t]["fks"]:
            # (id, seq, ref_table, from_col, to_col, ...)
            ref_table = fk[2]
            from_col = fk[3]
            to_col = fk[4]

            if ref_table in graph:
                graph[t].append((ref_table, from_col, to_col))
                graph[ref_table].append((t, to_col, from_col))  # 無向

    return graph


# =====================================================
#  BFS 取得 JOIN 順序
# =====================================================
def bfs_join_tables(root, graph):
    visited = set()
    queue = [root]
    order = []

    while queue:
        t = queue.pop(0)
        if t in visited:
            continue
        visited.add(t)
        order.append(t)

        for (to_table, _, _) in graph[t]:
            if to_table not in visited:
                queue.append(to_table)

    return order


# =====================================================
# 取 sample row
# =====================================================
def get_sample_row(db_path, table):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT * FROM {table} LIMIT 1;")
        row = cur.fetchone()
        if row is None:
            conn.close()
            return None

        cols = [c[0] for c in cur.description]
        conn.close()
        return dict(zip(cols, row))

    except:
        conn.close()
        return None


# =====================================================
# WHERE 子句生成（你的規則）
# =====================================================
def build_where_clause_text(value):
    safe = value.replace("'", "''")
    return f"LIKE '%{safe}%'"


def build_where_clause(sample_row, schema_cols):
    parts = []
    for colinfo in schema_cols:
        col_name = colinfo[1]
        col_type = colinfo[2]
        val = sample_row.get(col_name)

        if val is None:
            continue

        if isinstance(val, str):
            parts.append(f"t0.{col_name} {build_where_clause_text(val)}")
        else:
            parts.append(f"t0.{col_name} = {val}")

    if not parts:
        return ""
    return "WHERE " + " AND ".join(parts)


# =====================================================
# JOIN SQL 生成
# =====================================================
def generate_join_sql(root, join_order, schema, graph, sample_row):
    # 每個 table 分配 alias
    aliases = {t: f"t{i}" for i, t in enumerate(join_order)}

    sql_lines = []

    # SELECT
    select_parts = [f"{aliases[t]}.*" for t in join_order]
    sql_lines.append(f"SELECT {', '.join(select_parts)}")

    # FROM root
    sql_lines.append(f"FROM {root} {aliases[root]}")

    # JOIN 其他 table（依 BFS 順序建 parent）
    for t in join_order:
        if t == root:
            continue

        # 找 parent
        parent = None
        parent_fk = None

        for pt in join_order:
            if pt == t:
                break
            for (to_table, from_col, to_col) in graph[pt]:
                if to_table == t:
                    parent = pt
                    parent_fk = (from_col, to_col)
                    break
            if parent:
                break

        if not parent:
            continue

        p_alias = aliases[parent]
        t_alias = aliases[t]
        from_col, to_col = parent_fk

        sql_lines.append(
            f"LEFT JOIN {t} {t_alias} ON {p_alias}.{from_col} = {t_alias}.{to_col}"
        )

    # WHERE（只用 root t0）
    root_cols = schema[root]["columns"]
    where_sql = build_where_clause(sample_row, root_cols)
    if where_sql:
        sql_lines.append(where_sql)

    sql_lines.append("LIMIT 200;")

    return "\n".join(sql_lines)


# =====================================================
# SQL 驗證
# =====================================================
def validate_sql(db_path, sql):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        cur.fetchall()
        conn.close()
        return True
    except Exception as e:
        print("   ❌ SQL failed:", e)
        return False


# =====================================================
# LLM 產生 question
# =====================================================
def llm_generate_question(model, sql):
    prompt = (
        "請根據以下 SQL 查詢內容，以不推論、不自行延伸、不加入推測語意為前提，"
        "用自然的繁體中文寫出「這段 SQL 的查詢問題敘述」。請專注 SQL 實際內容。\n\n"
        f"SQL:\n{sql}\n\n請只輸出問題："
    )

    res = model.get_ans(prompt, temperature=0)
    if not res:
        return "查詢資料"
    return res.strip()


# =====================================================
# Schema text（用於 prompt）
# =====================================================
def generate_schema_description(schema):
    lines = ["/* 給定以下資料庫 schema: */\n"]

    for t, info in schema.items():
        lines.append(f"-- {t}")
        lines.append("CREATE TABLE %s (" % t)

        col_defs = []
        for col in info["columns"]:
            cname = col[1]
            ctype = col[2]
            col_defs.append(f"  {cname} {ctype}")
        lines.append(",\n".join(col_defs))
        lines.append(");\n")

        # 外鍵
        if info["fks"]:
            lines.append("/* FOREIGN KEYS:")
            for fk in info["fks"]:
                lines.append(f" * {t}.{fk[3]} -> {fk[2]}.{fk[4]}")
            lines.append(" */\n")

    return "\n".join(lines)


# =====================================================
# 為 table 產生 few-shot
# =====================================================
def generate_fewshot_for_table(table, db_path, schema, graph, model, db_name):
    print(f"\n🧩 處理 table: {table}")

    sample = get_sample_row(db_path, table)
    if not sample:
        print("   ⚠️ 無資料，跳過")
        return None

    join_order = bfs_join_tables(table, graph)

    sql = generate_join_sql(table, join_order, schema, graph, sample)

    if not validate_sql(db_path, sql):
        return None

    question = llm_generate_question(model, sql)

    schema_desc = generate_schema_description(schema)
    full_prompt = f"{schema_desc}\n\n/* 回答以下問題：{question} */\n{sql}"

    return {
        "question": question,
        "db_id": db_name,
        "prompt": full_prompt
    }


# =====================================================
# main()
# =====================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_root_directory", type=str, required=True)
    parser.add_argument("--model", type=str, default="gpt-4o")
    args = parser.parse_args()

    db_name = args.db_root_directory
    db_path = f"{db_name}/dev/dev_databases/{db_name}/{db_name}.sqlite"

    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫：{db_path}")
        return

    _logger = Logger(db_id="auto_fewshot", question_id=0, result_directory="logs")

    print("🔧 初始化 LLM...")
    model = model_chose("auto_fewshot", args.model)

    print("📊 讀取 SQLite schema...")
    tables, schema = analyze_database(db_path)

    print("🔗 建立 FK Graph...")
    graph = build_fk_graph(tables, schema)

    fewshots = []

    print("\n🚀 開始生成 few-shot...")
    for t in tables:
        fs = generate_fewshot_for_table(t, db_path, schema, graph, model, db_name)
        if fs:
            fewshots.append(fs)

    # output
    output_path = Path(db_name) / "fewshot" / "questions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "extract": {},
        "parse": {},
        "questions": fewshots
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 完成！few-shot 已輸出到: {output_path}")
    print(f"✔ 產生 {len(fewshots)} 筆 few-shot")


if __name__ == "__main__":
    main()
