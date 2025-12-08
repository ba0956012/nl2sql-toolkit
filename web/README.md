# Web 介面

這個目錄包含所有的 Web 介面和 API 服務。

## 檔案說明

### api_server.py
- REST API 伺服器
- 提供查詢 API 端點
- Port: 5000

### web_interface.py
- 主要的 Web 查詢介面
- 提供完整的查詢功能和結果展示
- Port: 5002
- **Docker 預設啟動**

### fewshot_web.py
- Few-shot 簡易管理介面
- 基本的 CRUD 操作
- Port: 5001

### fewshot_advanced.py
- Few-shot 進階管理介面
- 支援編輯 extract, parse, questions 三個部分
- 提供 SQL 驗證功能
- Port: 5003
- **Docker 服務: fewshot-manager**

## 啟動方式

### 本地開發
```bash
# 主要 Web 介面
python web/web_interface.py

# Few-shot 管理介面
python web/fewshot_advanced.py

# API 伺服器
python web/api_server.py
```

### Docker
```bash
# 啟動所有服務
docker-compose up -d

# 只啟動主介面
docker-compose up opensearch-sql

# 只啟動 Few-shot 管理
docker-compose up fewshot-manager
```

## 訪問地址

- 主介面: http://localhost:5002
- Few-shot 管理: http://localhost:5004 (Docker) 或 http://localhost:5003 (本地)
- API: http://localhost:5000
