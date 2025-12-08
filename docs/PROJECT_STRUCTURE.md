# 專案結構整理建議

## 目前問題
- 根目錄有 30+ 個檔案，難以管理
- 工具腳本、測試檔案、Web 介面混在一起
- 文檔檔案散落各處

## 建議的新結構

```
OpenSearch-SQL/
├── src/                          # 核心程式碼（保持不變）
│   ├── config.py
│   ├── llm/
│   ├── pipeline/
│   └── runner/
│
├── web/                          # 🆕 Web 介面
│   ├── api_server.py            # API 伺服器
│   ├── web_interface.py         # 主要 Web 介面
│   ├── fewshot_web.py           # Few-shot 簡易管理
│   └── fewshot_advanced.py      # Few-shot 進階管理
│
├── scripts/                      # 🆕 工具腳本
│   ├── setup/                   # 設置腳本
│   │   ├── setup_env.sh
│   │   └── setup_from_sqlite_with_fewshot.sh
│   ├── fewshot/                 # Few-shot 管理
│   │   ├── auto_generate_fewshot.py
│   │   ├── manage_fewshot.py
│   │   ├── sync_fewshot.py
│   │   └── test_fewshot_format.py
│   ├── chromadb/                # ChromaDB 管理
│   │   ├── build_chromadb_index.py
│   │   ├── manage_chromadb.py
│   │   └── test_chromadb_retrieval.py
│   └── utils/                   # 其他工具
│       ├── create_custom_db_template.py
│       ├── analyze_failure.py
│       └── analyze_fewshot_usage.py
│
├── tests/                        # 🆕 測試檔案
│   ├── test_query_interface.py
│   ├── test_fewshot_retrieval.py
│   ├── test_chromadb_retrieval.py
│   └── debug_query_result.py
│
├── docs/                         # 🆕 文檔
│   ├── FEWSHOT_ANALYSIS.md
│   ├── FEWSHOT_RETRIEVAL.md
│   ├── CHROMADB_MIGRATION.md
│   └── PROJECT_STRUCTURE.md
│
├── tools/                        # 現有工具目錄（保持）
├── PosTest/                      # 資料庫（保持）
├── results/                      # 結果（保持）
├── logs/                         # 日誌（保持）
├── model/                        # 模型（保持）
│
├── query_interface.py            # 主要查詢介面（保持在根目錄）
├── docker-compose.yml            # Docker 配置（保持）
├── Dockerfile                    # Docker 配置（保持）
├── requirements.txt              # 依賴（保持）
├── .env                          # 環境變數（保持）
├── .env.example                  # 環境變數範例（保持）
├── readme.md                     # 主要文檔（保持）
└── LICENSE                       # 授權（保持）
```

## 整理步驟

### 1. 創建新目錄
```bash
mkdir -p web scripts/{setup,fewshot,chromadb,utils} tests docs
```

### 2. 移動 Web 介面
```bash
mv api_server.py web/
mv web_interface.py web/
mv fewshot_web.py web/
mv fewshot_advanced.py web/
```

### 3. 移動腳本
```bash
# 設置腳本
mv setup_env.sh scripts/setup/
mv setup_from_sqlite_with_fewshot.sh scripts/setup/

# Few-shot 管理
mv auto_generate_fewshot.py scripts/fewshot/
mv manage_fewshot.py scripts/fewshot/
mv sync_fewshot.py scripts/fewshot/
mv test_fewshot_format.py scripts/fewshot/

# ChromaDB 管理
mv build_chromadb_index.py scripts/chromadb/
mv manage_chromadb.py scripts/chromadb/
mv test_chromadb_retrieval.py scripts/chromadb/

# 工具
mv create_custom_db_template.py scripts/utils/
mv analyze_failure.py scripts/utils/
mv analyze_fewshot_usage.py scripts/utils/
```

### 4. 移動測試
```bash
mv test_query_interface.py tests/
mv test_fewshot_retrieval.py tests/
mv debug_query_result.py tests/
mv test_logs.sh tests/
```

### 5. 移動文檔
```bash
mv FEWSHOT_ANALYSIS.md docs/
mv FEWSHOT_RETRIEVAL.md docs/
mv CHROMADB_MIGRATION.md docs/
```

## 需要更新的檔案

整理後需要更新以下檔案中的路徑引用：

1. **docker-compose.yml** - 更新 web 服務的啟動命令
2. **README.md** - 更新文檔連結和使用說明
3. **各個腳本** - 更新相對路徑的 import

## 優點

✅ 根目錄更清爽，只保留核心配置檔案
✅ 相關功能集中管理，易於查找
✅ 測試和文檔分離，結構更清晰
✅ 便於新成員理解專案結構
✅ 符合 Python 專案最佳實踐
