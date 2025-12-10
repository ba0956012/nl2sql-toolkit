# NL2SQL Toolkit

基於 [OpenSearch-SQL](https://github.com/OpenSearch-AI/OpenSearch-SQL) 的 Text-to-SQL 工具，用於將自然語言問題轉換為 SQL 查詢，並提供 Web 查詢介面與 Few-shot 管理功能。

---

## 快速開始

```bash
# 1. 設置配置
cp .env.example .env && nano .env

# 2. 建立資料庫 + Few-shot
bash scripts/setup/setup_from_sqlite_with_fewshot.sh MyDB /path/to/your.sqlite

# 3. 啟動服務
docker-compose up
```

介面：

- 查詢界面：http://localhost:5002  
- Few-shot 管理：http://localhost:5003  

---

## Text-to-SQL 簡介

Text-to-SQL 用於將自然語言問題轉換為 SQL 查詢。

範例：

```
問題：哪個商品銷量最高？
系統：SELECT product_name, SUM(amount) ...
```

---

# 功能介紹

## 核心功能  
- 將自然語言查詢自動生成 SQL  
- Web 查詢介面  
- Few-shot 範例管理  
- 自訂 Few-shot 增加查詢準確度  

## 擴充功能
- 自動化建置流程（包含 Few-shot 自動生成）
- 動態選擇fewshot範例
- `.env` 統一環境設定
- Docker 一鍵部署

---

# 主要新增

## 1. 自動建置流程

執行以下指令即可完成所有設定：

```bash
sh setup_from_sqlite_with_fewshot.sh MyDB /path/to/db.sqlite
```

流程包含：

- 資料庫結構建立  
- 生成資料表描述  
- 資料前處理  
- 自動產生 Few-shot  
- Embedding 建立  
- 完整檢查流程  

---

## 2. 動態 Few-shot 選擇（ChromaDB）

系統啟動時會將 Few-shot 內容建立向量索引，查詢時會自動選擇最相似的範例。

流程如下：

```
使用者問題 → ChromaDB 檢索 → 選取 Few-shot → 生成 SQL
```

特色：

- Few-shot 修改後自動更新索引  
- Embedding 永久儲存  
- 不須重新計算  
- 提升 SQL 生成可靠度  

---

## 3. `.env` 統一配置

可設定：

- Azure OpenAI / OpenAI API Key  
- Web 服務 Port  
- DB Root Path  
- 模型設定  
- Few-shot 資料來源  
- Embedding 選項  

---

# 使用方式

## 1. 設定 `.env`

```bash
cp .env.example .env
nano .env
```

最小設定：

```env
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
DB_ROOT_DIRECTORY=MyDB
```

---

## 2. 建立資料庫與 Few-shot

```bash
bash scripts/setup/setup_from_sqlite_with_fewshot.sh MyDB /path/to/your.sqlite
```

---

## 3. 啟動 Web 介面

```bash
docker-compose up
```


# 專案結構

```
OpenSearch-SQL/
├── src/
│   ├── config.py
│   ├── llm/
│   ├── pipeline/
│   └── runner/
│
├── web/
│   ├── web_interface.py
│   ├── fewshot_advanced.py
│   ├── api_server.py
│   └── fewshot_web.py
│
├── scripts/
│   ├── setup/
│   ├── fewshot/
│   ├── chromadb/
│   └── utils/
│
├── query_interface.py
├── docker-compose.yml
├── .env.example
└── .env
```

---
