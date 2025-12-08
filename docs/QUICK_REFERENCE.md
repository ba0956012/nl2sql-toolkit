# 快速參考指南

## 常用命令

### 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 只啟動主介面
docker-compose up opensearch-sql -d

# 只啟動 Few-shot 管理
docker-compose up fewshot-manager -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 本地開發

```bash
# 主查詢介面
python web/web_interface.py

# Few-shot 管理
python web/fewshot_advanced.py

# API 伺服器
python web/api_server.py

# 命令行查詢
python query_interface.py "你的問題"
```

### Few-shot 管理

```bash
# 自動生成範例
python scripts/fewshot/auto_generate_fewshot.py

# 同步資料
python scripts/fewshot/sync_fewshot.py

# 驗證格式
python scripts/fewshot/test_fewshot_format.py
```

### ChromaDB 管理

```bash
# 建立索引
python scripts/chromadb/build_chromadb_index.py

# 管理資料
python scripts/chromadb/manage_chromadb.py

# 測試檢索
python scripts/chromadb/test_chromadb_retrieval.py
```

### 測試和調試

```bash
# 測試查詢
python tests/test_query_interface.py

# 測試 Few-shot 檢索
python tests/test_fewshot_retrieval.py

# 調試查詢結果
python tests/debug_query_result.py
```

### 初始化新資料庫

```bash
# 完整設置（包含 Few-shot）
bash scripts/setup/setup_from_sqlite_with_fewshot.sh DB_NAME /path/to/db.sqlite

# 只設置環境
bash scripts/setup/setup_env.sh
```

## 常用路徑

### 配置檔案
- `.env` - 環境變數配置
- `docker-compose.yml` - Docker 服務配置

### 資料庫檔案
- `{DB_NAME}/dev/dev_databases/{DB_NAME}/{DB_NAME}.sqlite` - SQLite 資料庫
- `{DB_NAME}/dev/dev.json` - 資料集配置
- `{DB_NAME}/dev/tables.json` - 表格結構

### Few-shot 檔案
- `{DB_NAME}/fewshot/questions.json` - Few-shot 範例
- `{DB_NAME}/.chromadb/` - ChromaDB 向量資料庫

### 結果和日誌
- `results/` - 查詢結果
- `logs/` - 系統日誌

## 訪問地址

### Docker 部署
- 主介面: http://localhost:5002
- Few-shot 管理: http://localhost:5004
- API: http://localhost:5000

### 本地開發
- 主介面: http://localhost:5002
- Few-shot 管理: http://localhost:5003
- API: http://localhost:5000

## 環境變數

### 必需
```env
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-key
```

### 可選
```env
DB_ROOT_DIRECTORY=PosTest
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.0
MAX_TOKENS=800
```

## 故障排除

### 服務無法啟動
```bash
# 檢查日誌
docker-compose logs

# 重新建立
docker-compose down
docker-compose up --build
```

### Few-shot 檢索失敗
```bash
# 重建 ChromaDB 索引
python scripts/chromadb/build_chromadb_index.py

# 驗證 Few-shot 格式
python scripts/fewshot/test_fewshot_format.py
```

### 查詢失敗
```bash
# 調試查詢
python tests/debug_query_result.py

# 檢查日誌
tail -f logs/*.log
```

## 更多資訊

- [專案結構](PROJECT_STRUCTURE.md)
- [Few-shot 檢索](FEWSHOT_RETRIEVAL.md)
- [ChromaDB 遷移](CHROMADB_MIGRATION.md)
- [主要文檔](../readme.md)
