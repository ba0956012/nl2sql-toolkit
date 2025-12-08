#!/bin/bash
# 從 SQLite 檔案建立完整的資料庫設置（包含自動生成 fewshot）
# 使用方式: sh setup_from_sqlite_with_fewshot.sh <DB_NAME> <SQLITE_PATH>

set -e  # 遇到錯誤立即退出

# 檢查參數
if [ $# -lt 2 ]; then
    echo "使用方式: sh setup_from_sqlite_with_fewshot.sh <DB_NAME> <SQLITE_PATH>"
    echo ""
    echo "範例:"
    echo "  sh setup_from_sqlite_with_fewshot.sh MyDB /path/to/your.sqlite"
    exit 1
fi

DB_NAME=$1
SQLITE_PATH=$2

echo "========================================"
echo "  從 SQLite 建立完整設置（含 Fewshot）"
echo "========================================"
echo "資料庫名稱: $DB_NAME"
echo "SQLite 檔案: $SQLITE_PATH"
echo ""

# 檢查 SQLite 檔案是否存在
if [ ! -f "$SQLITE_PATH" ]; then
    echo "❌ 錯誤: 找不到 SQLite 檔案: $SQLITE_PATH"
    exit 1
fi

# ============================================
# 步驟 1: 建立基本結構
# ============================================
echo "========================================"
echo "步驟 1: 建立基本結構"
echo "========================================"
echo ""

python scripts/utils/create_custom_db_template.py \
    --db_name "$DB_NAME" \
    --db_path "$SQLITE_PATH"

if [ $? -ne 0 ]; then
    echo "❌ 步驟 1 失敗"
    exit 1
fi

echo ""
echo "✅ 步驟 1 完成"
echo ""

# ============================================
# 步驟 2: 生成 database_description
# ============================================
echo "========================================"
echo "步驟 2: 生成 database_description"
echo "========================================"
echo ""

python tools/generate_database_descriptions.py \
    --database "$DB_NAME/dev/dev_databases/$DB_NAME/$DB_NAME.sqlite" \
    --output "$DB_NAME/dev/dev_databases/$DB_NAME/database_description/"

if [ $? -ne 0 ]; then
    echo "❌ 步驟 2 失敗"
    exit 1
fi

echo ""
echo "✅ 步驟 2 完成"
echo ""

# ============================================
# 步驟 3: 生成 tables.json
# ============================================
echo "========================================"
echo "步驟 3: 生成 tables.json"
echo "========================================"
echo ""

mkdir -p "$DB_NAME/data_preprocess"

python tools/generate_tables_json.py \
    --database "$DB_NAME/dev/dev_databases/$DB_NAME/$DB_NAME.sqlite" \
    --db-id "$DB_NAME" \
    --output "$DB_NAME/data_preprocess/tables.json"

if [ $? -ne 0 ]; then
    echo "❌ 步驟 3 失敗"
    exit 1
fi

# 複製到需要的位置
cp "$DB_NAME/data_preprocess/tables.json" "$DB_NAME/dev/dev_tables.json"
cp "$DB_NAME/data_preprocess/tables.json" "$DB_NAME/train/train_tables.json"

echo ""
echo "✅ 步驟 3 完成"
echo ""

# ============================================
# 步驟 4: 準備訓練資料（空的）
# ============================================
echo "========================================"
echo "步驟 4: 準備訓練資料"
echo "========================================"
echo ""

# train.json 已經由 create_custom_db_template.py 創建（空的）
# 複製到 data_preprocess
cp "$DB_NAME/train/train.json" "$DB_NAME/data_preprocess/train.json"

echo "⚠️  train.json 是空的，預處理會跳過"
echo ""
echo "✅ 步驟 4 完成"
echo ""

# ============================================
# 步驟 5: 資料預處理（不含 Embedding）
# ============================================
echo "========================================"
echo "步驟 5: 資料預處理"
echo "========================================"
echo ""

python src/database_process/data_preprocess.py \
    --db_root_directory "$DB_NAME" \
    --dev_json "dev/dev.json" \
    --train_json "train/train.json" \
    --dev_table "dev/dev_tables.json" \
    --train_table "train/train_tables.json"

if [ $? -ne 0 ]; then
    echo "❌ 資料預處理失敗"
    exit 1
fi

echo ""
echo "✅ 步驟 5 完成"
echo ""

# ============================================
# 步驟 6: 自動生成 Few-shot（提前到 Embedding 之前）
# ============================================
echo "========================================"
echo "步驟 6: 自動生成 Few-shot"
echo "========================================"
echo ""

echo "🤖 使用 LLM 自動生成 Few-shot 範例..."
echo "   （這是查詢系統的重要組成部分）"
echo ""

python scripts/fewshot/auto_generate_fewshot.py \
    --db_root_directory "$DB_NAME" \
    --model "gpt-4o"

if [ $? -ne 0 ]; then
    echo "⚠️  自動生成失敗，將使用空的 fewshot"
    echo "   你可以稍後手動添加範例"
    echo "   或使用 fewshot 管理界面: python fewshot_advanced.py"
else
    echo ""
    echo "✅ Few-shot 自動生成完成"
    echo ""
    
    # 同步生成 extract 和 parse 資料
    echo "🔄 生成 extract 和 parse 資料..."
    python scripts/fewshot/sync_fewshot.py import "$DB_NAME"
    python scripts/fewshot/sync_fewshot.py export "$DB_NAME"
    
    if [ $? -ne 0 ]; then
        echo "⚠️  同步失敗"
    else
        echo "✅ extract 和 parse 資料已生成"
    fi
    
    # 建立 ChromaDB 索引
    echo "🔍 建立 ChromaDB 索引..."
    python scripts/chromadb/build_chromadb_index.py --db-root "$DB_NAME"
    
    if [ $? -ne 0 ]; then
        echo "⚠️  ChromaDB 索引建立失敗或跳過"
        echo "   系統仍可使用，但檢索速度較慢"
    fi
    
    echo ""
    
    # 驗證格式
    echo "🔍 驗證 Few-shot 格式..."
    python scripts/fewshot/test_fewshot_format.py "$DB_NAME"
    
    if [ $? -ne 0 ]; then
        echo "⚠️  格式驗證失敗，請檢查"
    fi
fi

echo ""
echo "✅ 步驟 6 完成"
echo ""

# ============================================
# 步驟 7: 生成 Embedding（在 Few-shot 之後）
# ============================================
echo "========================================"
echo "步驟 7: 生成 Embedding"
echo "========================================"
echo ""
echo "這可能需要幾分鐘..."
echo ""

python src/database_process/make_emb.py \
    --db_root_directory "$DB_NAME" \
    --dev_database "dev/dev_databases" \
    --bert_model "all-MiniLM-L6-v2"

if [ $? -ne 0 ]; then
    echo "❌ Embedding 生成失敗"
    exit 1
fi

echo ""
echo "✅ 步驟 7 完成"
echo ""

# ============================================
# 完成
# ============================================
echo ""
echo "========================================"
echo "  ✅ 設置完成！"
echo "========================================"
echo ""

echo "📁 生成的目錄結構:"
echo ""
tree -L 3 "$DB_NAME" 2>/dev/null || find "$DB_NAME" -type d | head -20

echo ""
echo "📊 檢查關鍵檔案:"
echo ""

check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1 ($(du -h "$1" | cut -f1))"
    else
        echo "❌ $1 (不存在)"
    fi
}

check_file "$DB_NAME/dev/dev.json"
check_file "$DB_NAME/dev/dev_tables.json"
check_file "$DB_NAME/train/train.json"
check_file "$DB_NAME/fewshot/questions.json"
check_file "$DB_NAME/data_preprocess/tables.json"
check_file "$DB_NAME/emb/$DB_NAME.pkl.gz"
check_file "$DB_NAME/emb/${DB_NAME}_value.pkl.gz"

echo ""
echo "========================================"
echo "  下一步"
echo "========================================"
echo ""
echo "1. 測試查詢:"
echo "   python tests/test_query_interface.py --db-root-path $DB_NAME"
echo ""
echo "2. 或使用 Web 界面:"
echo "   python web/web_interface.py"
echo "   # 在瀏覽器開啟 http://localhost:5002"
echo ""
echo "3. 編輯 Few-shot 範例:"
echo "   python web/fewshot_advanced.py"
echo "   # 在瀏覽器開啟 http://localhost:5003"
echo ""
echo "4. 使用 Docker 測試:"
echo "   docker-compose up"
echo ""
echo "5. 清理測試資料:"
echo "   rm -rf $DB_NAME"
echo ""

echo "🎉 設置完成！"
