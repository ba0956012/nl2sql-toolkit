# 工具腳本

這個目錄包含各種管理和工具腳本。

## 目錄結構

### setup/
系統設置和初始化腳本
- `setup_env.sh` - 環境設置腳本
- `setup_from_sqlite_with_fewshot.sh` - 從 SQLite 建立專案並初始化 few-shot

### fewshot/
Few-shot 範例管理工具
- `auto_generate_fewshot.py` - 自動生成 few-shot 範例
- `manage_fewshot.py` - 命令行管理工具
- `sync_fewshot.py` - 同步 few-shot 資料
- `test_fewshot_format.py` - 驗證 few-shot 格式

### chromadb/
ChromaDB 向量資料庫管理
- `build_chromadb_index.py` - 建立 ChromaDB 索引
- `manage_chromadb.py` - 管理 ChromaDB 資料
- `test_chromadb_retrieval.py` - 測試檢索功能

### utils/
其他實用工具
- `create_custom_db_template.py` - 創建自訂資料庫模板
- `analyze_failure.py` - 分析查詢失敗原因
- `analyze_fewshot_usage.py` - 分析 few-shot 使用情況

## 使用範例

### 初始化專案
```bash
bash scripts/setup/setup_from_sqlite_with_fewshot.sh your_database.sqlite
```

### 管理 Few-shot
```bash
# 自動生成範例
python scripts/fewshot/auto_generate_fewshot.py

# 同步資料
python scripts/fewshot/sync_fewshot.py
```

### 建立 ChromaDB 索引
```bash
python scripts/chromadb/build_chromadb_index.py
```

### 分析工具
```bash
# 分析失敗查詢
python scripts/utils/analyze_failure.py

# 分析 few-shot 使用
python scripts/utils/analyze_fewshot_usage.py
```
