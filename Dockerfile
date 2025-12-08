# OpenSearch-SQL Docker Image
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼和資料
COPY . .

# 確保資料庫目錄存在
RUN mkdir -p PosTest/dev/dev_databases/PosTest \
    && mkdir -p logs \
    && mkdir -p results

# 驗證資料庫文件存在
RUN if [ -f "PosTest/dev/dev_databases/PosTest/PosTest.sqlite" ]; then \
        echo "✅ 資料庫文件已包含"; \
        sqlite3 PosTest/dev/dev_databases/PosTest/PosTest.sqlite "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" || echo "⚠️ 資料庫可能損壞"; \
    else \
        echo "⚠️ 警告: 資料庫文件不存在"; \
    fi

# 驗證配置文件
RUN if [ -f "azure_openai_config.py" ]; then \
        echo "✅ Azure OpenAI 配置文件已包含"; \
    else \
        echo "⚠️ 警告: Azure OpenAI 配置文件不存在，請掛載或創建"; \
    fi

# 設置權限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 5002

# 設置環境變量
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# 啟動命令
CMD ["python", "web/web_interface.py"]
