#!/bin/bash
# 一鍵設置新資料集
# 使用方法: sh tools/setup_new_dataset.sh MyDB MyDB/dev/dev_databases/MyDB/MyDB.sqlite

set -e  # 遇到錯誤立即退出

# 檢查參數
if [ $# -lt 2 ]; then
    echo "使用方法: sh tools/setup_new_dataset.sh <DB_NAME> <SQLITE_PATH>"
    echo ""
    echo "範例:"
    echo "  sh tools/setup_new_dataset.sh MyDB MyDB/dev/dev_databases/MyDB/MyDB.sqlite"
    exit 1
fi

DB_NAME=$1
SQLITE_PATH=$2

echo "========================================"
echo "  設置新資料集: $DB_NAME"
echo "========================================"
echo "資料庫路徑: $SQLITE_PATH"
echo ""

# 檢查資料庫文件是否存在
if [ ! -f "$SQLITE_PATH" ]; then
    echo "❌ 錯誤: 資料庫文件不存在: $SQLITE_PATH"
    exit 1
fi

# 創建目錄結構
echo "步驟 1: 創建目錄結構..."
mkdir -p "$DB_NAME/dev/dev_databases/$DB_NAME"
mkdir -p "$DB_NAME/train/train_databases/$DB_NAME"
mkdir -p "$DB_NAME/fewshot"
mkdir -p "$DB_NAME/data_preprocess"
mkdir -p "$DB_NAME/emb"
echo "✅ 目錄創建完成"

# 複製資料庫文件（如果不在正確位置）
TARGET_DB="$DB_NAME/dev/dev_databases/$DB_NAME/$DB_NAME.sqlite"
if [ "$SQLITE_PATH" != "$TARGET_DB" ]; then
    echo ""
    echo "步驟 2: 複製資料庫文件..."
    cp "$SQLITE_PATH" "$TARGET_DB"
    echo "✅ 資料庫複製完成"
    SQLITE_PATH="$TARGET_DB"
fi

# 生成 database_description
echo ""
echo "步驟 3: 生成 database_description..."
python tools/generate_database_descriptions.py \
    --database "$SQLITE_PATH" \
    --output "$DB_NAME/dev/dev_databases/$DB_NAME/database_description/"

# 生成 tables.json
echo ""
echo "步驟 4: 生成 tables.json..."
python tools/generate_tables_json.py \
    --database "$SQLITE_PATH" \
    --db-id "$DB_NAME" \
    --output "$DB_NAME/data_preprocess/tables.json"

# 創建空的 dev.json
echo ""
echo "步驟 5: 創建 dev.json 模板..."
cat > "$DB_NAME/dev/dev.json" << EOF
[
    {
        "question_id": 0,
        "db_id": "$DB_NAME",
        "question": "範例問題：有多少筆記錄？",
        "raw_question": "範例問題：有多少筆記錄？",
        "evidence": "",
        "SQL": "SELECT COUNT(*) FROM your_table",
        "difficulty": "simple"
    }
]
EOF
echo "✅ dev.json 模板創建完成"

# 創建空的 fewshot
echo ""
echo "步驟 6: 創建 fewshot 模板..."
cat > "$DB_NAME/fewshot/questions.json" << EOF
[
    {
        "question_id": 0,
        "db_id": "$DB_NAME",
        "question": "範例問題：有多少筆記錄？",
        "raw_question": "範例問題：有多少筆記錄？",
        "evidence": "",
        "SQL": "SELECT COUNT(*) FROM your_table",
        "difficulty": "simple"
    }
]
EOF
echo "✅ fewshot 模板創建完成"

# 創建預處理腳本
echo ""
echo "步驟 7: 創建預處理腳本..."
cat > "$DB_NAME/preprocess.sh" << EOF
#!/bin/bash
# 預處理 $DB_NAME 資料庫

db_root_directory=$DB_NAME
dev_json=dev/dev.json
train_json=train/train.json
dev_table=dev/dev_tables.json
train_table=train/train_tables.json
dev_database=dev/dev_databases
bert_model=all-MiniLM-L6-v2

echo "開始預處理 $DB_NAME 資料庫..."

# 基本預處理
python -u src/database_process/data_preprocess.py \\
    --db_root_directory "\${db_root_directory}" \\
    --dev_json "\${dev_json}" \\
    --train_json "\${train_json}" \\
    --dev_table "\${dev_table}" \\
    --train_table "\${train_table}"

# 生成 embeddings
python -u src/database_process/make_emb.py \\
    --db_root_directory "\${db_root_directory}" \\
    --dev_database "\${dev_database}" \\
    --bert_model "\${bert_model}"

echo "✅ 預處理完成！"
EOF
chmod +x "$DB_NAME/preprocess.sh"
echo "✅ 預處理腳本創建完成"

# 創建查詢腳本
echo ""
echo "步驟 8: 創建查詢腳本..."
cat > "$DB_NAME/query.sh" << EOF
#!/bin/bash
# 查詢 $DB_NAME 資料庫

if [ \$# -eq 0 ]; then
    echo "使用方法:"
    echo "  sh $DB_NAME/query.sh \"你的問題\""
    exit 1
fi

QUESTION="\$*"

# 使用查詢接口
python query_interface.py "\$QUESTION" --db-root-path "$DB_NAME"
EOF
chmod +x "$DB_NAME/query.sh"
echo "✅ 查詢腳本創建完成"

# 完成
echo ""
echo "========================================"
echo "  ✅ 設置完成！"
echo "========================================"
echo ""
echo "📁 創建的文件和目錄:"
echo "  $DB_NAME/"
echo "  ├── dev/"
echo "  │   ├── dev.json"
echo "  │   └── dev_databases/$DB_NAME/"
echo "  │       ├── $DB_NAME.sqlite"
echo "  │       └── database_description/"
echo "  ├── fewshot/"
echo "  │   └── questions.json"
echo "  ├── data_preprocess/"
echo "  │   └── tables.json"
echo "  ├── preprocess.sh"
echo "  └── query.sh"
echo ""
echo "📝 下一步:"
echo ""
echo "1. 編輯 database_description 文件"
echo "   cd $DB_NAME/dev/dev_databases/$DB_NAME/database_description/"
echo "   # 為每個表添加詳細的列描述"
echo ""
echo "2. 編輯 dev.json 添加測試問題"
echo "   vi $DB_NAME/dev/dev.json"
echo ""
echo "3. 編輯 fewshot/questions.json 添加範例"
echo "   vi $DB_NAME/fewshot/questions.json"
echo "   # 建議添加 15-30 個範例"
echo ""
echo "4. 運行預處理"
echo "   sh $DB_NAME/preprocess.sh"
echo ""
echo "5. 測試查詢"
echo "   sh $DB_NAME/query.sh \"你的問題\""
echo ""
echo "💡 提示:"
echo "  - database_description 越詳細，查詢越準確"
echo "  - few-shot 範例要涵蓋不同難度和查詢類型"
echo "  - 使用 tools/validate_fewshot.py 驗證範例"
echo ""
