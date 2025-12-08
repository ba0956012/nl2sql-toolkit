# 完整測試指南

## 前置準備

### 1. 確認環境配置

檢查 `.env` 檔案：
```bash
cat .env | grep -E "AZURE_OPENAI|DB_ROOT"
```

應該看到：
```
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-key
DB_ROOT_DIRECTORY=TestDB
```

### 2. 確認資料庫存在

```bash
ls -la TestDB/dev/dev_databases/TestDB/TestDB.sqlite
ls -la TestDB/fewshot/questions.json
```

## 測試流程

### 步驟 1：清理舊資料（可選）

```bash
# 停止所有服務
docker-compose down

# 清理舊的容器和映像
docker-compose down --volumes --rmi local

# 清理結果和日誌
rm -rf results/* logs/*
```

### 步驟 2：建立新資料庫（如果需要）

```bash
# 從 SQLite 建立完整設置
bash scripts/setup/setup_from_sqlite_with_fewshot.sh TestDB ./path/to/your.sqlite
```

這會自動：
- ✅ 建立資料庫結構
- ✅ 生成 database_description
- ✅ 生成 tables.json
- ✅ 資料預處理
- ✅ 自動生成 Few-shot 範例
- ✅ 生成 Embedding
- ✅ 建立 ChromaDB 索引

### 步驟 3：啟動 Docker 服務

```bash
# 重新建立並啟動
docker-compose up --build

# 或背景執行
docker-compose up --build -d

# 查看日誌
docker-compose logs -f
```

### 步驟 4：驗證服務

#### 4.1 檢查服務狀態
```bash
docker-compose ps
```

應該看到兩個服務都在運行：
- `opensearch-sql-web` (port 5002)
- `opensearch-sql-fewshot` (port 5004)

#### 4.2 檢查健康狀態
```bash
curl http://localhost:5002/health
curl http://localhost:5004/health
```

#### 4.3 檢查環境變數
```bash
docker-compose exec opensearch-sql env | grep DB_ROOT
```

應該顯示：`DB_ROOT_DIRECTORY=TestDB`

#### 4.4 檢查 fewshot 資料
```bash
docker-compose exec opensearch-sql python -c "
import json
with open('TestDB/fewshot/questions.json', 'r') as f:
    data = json.load(f)
    print('Questions:', len(data.get('questions', [])))
    print('Extract:', len(data.get('extract', {})))
    print('Parse:', len(data.get('parse', {})))
"
```

### 步驟 5：測試 Web 介面

#### 5.1 主查詢介面
1. 訪問 http://localhost:5002
2. 輸入問題，例如：「查詢所有商品」
3. 點擊「查詢」
4. 檢查是否生成 SQL
5. 點擊「執行 SQL」查看結果

#### 5.2 Few-shot 管理介面
1. 訪問 http://localhost:5004
2. 應該看到現有的 few-shot 範例列表
3. 點擊「新增範例」測試新增功能
4. 編輯現有範例測試修改功能
5. 檢查數量是否正確

### 步驟 6：測試 Few-shot 檢索

```bash
docker-compose exec opensearch-sql python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')
from pathlib import Path
from runner.fewshot_retriever_chroma import get_retriever

fewshot_path = Path('TestDB') / 'fewshot' / 'questions.json'
retriever = get_retriever(str(fewshot_path))

# 測試不同問題
test_questions = [
    '查詢所有商品',
    '統計銷售總額',
    '查詢門市資訊'
]

for q in test_questions:
    qid = retriever.get_best_question_id(q)
    print(f'問題: {q} -> Few-shot #{qid}')
"
```

### 步驟 7：測試命令行介面

```bash
# 單次查詢
python query_interface.py "查詢所有商品"

# 互動模式
python query_interface.py
```

### 步驟 8：測試 ChromaDB 自動更新

1. 在 http://localhost:5004 修改一個 few-shot 範例
2. 在 http://localhost:5002 執行查詢
3. 檢查日誌是否顯示 "Few-shot data updated, rebuilding ChromaDB index..."

```bash
docker-compose logs opensearch-sql | grep "Few-shot data updated"
```

## 常見問題排查

### 問題 1：服務無法啟動

```bash
# 檢查日誌
docker-compose logs

# 檢查端口是否被佔用
lsof -i :5002
lsof -i :5004

# 重新建立
docker-compose down
docker-compose up --build
```

### 問題 2：找不到資料庫

```bash
# 檢查容器內的檔案
docker-compose exec opensearch-sql ls -la TestDB/dev/dev_databases/TestDB/

# 檢查環境變數
docker-compose exec opensearch-sql env | grep DB_ROOT
```

### 問題 3：Few-shot 為空

```bash
# 檢查檔案內容
docker-compose exec opensearch-sql cat TestDB/fewshot/questions.json | head -20

# 重新生成
python scripts/fewshot/auto_generate_fewshot.py --db_root_directory TestDB
```

### 問題 4：ChromaDB 索引問題

```bash
# 重建索引
python scripts/chromadb/build_chromadb_index.py --db-root TestDB

# 檢查索引
python scripts/chromadb/manage_chromadb.py stats TestDB
```

### 問題 5：SQL 執行失敗

```bash
# 檢查資料庫路徑
docker-compose exec opensearch-sql python -c "
import os
db_root = os.getenv('DB_ROOT_DIRECTORY', 'PosTest')
db_path = f'{db_root}/dev/dev_databases/{db_root}/{db_root}.sqlite'
print('DB Path:', db_path)
import os.path
print('Exists:', os.path.exists(db_path))
"
```

## 效能測試

### 測試 ChromaDB 檢索速度

```bash
python scripts/chromadb/test_chromadb_retrieval.py TestDB
```

### 測試查詢端到端

```bash
python tests/test_query_interface.py --db-root-path TestDB
```

## 清理

### 停止服務
```bash
docker-compose down
```

### 完全清理
```bash
# 停止並刪除容器、網路、映像
docker-compose down --volumes --rmi local

# 清理結果和日誌
rm -rf results/* logs/*

# 清理 ChromaDB（如果要重建）
rm -rf TestDB/.chromadb
```

## 成功標準

✅ 所有服務正常啟動
✅ 健康檢查通過
✅ Web 介面可以訪問
✅ Few-shot 管理介面顯示正確數量
✅ 查詢可以生成 SQL
✅ SQL 可以執行並返回結果
✅ Few-shot 檢索選擇合適的範例
✅ ChromaDB 自動更新正常工作

## 下一步

- 添加更多 few-shot 範例以提高準確度
- 調整模型參數（temperature, top_p）
- 測試不同類型的查詢
- 監控查詢效能和準確度
