#!/bin/bash
# 快速設置環境配置

echo "========================================"
echo "  環境配置設置"
echo "========================================"
echo ""

# 檢查 .env 是否存在
if [ -f ".env" ]; then
    echo "⚠️  .env 檔案已存在"
    read -p "是否要覆蓋？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消設置"
        exit 1
    fi
    # 備份現有的 .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已備份現有 .env"
fi

# 複製範本
cp .env.example .env
echo "✅ 已創建 .env 檔案"
echo ""

# 互動式設置
echo "請輸入你的配置（按 Enter 跳過）："
echo ""

# Azure OpenAI
read -p "Azure OpenAI Endpoint: " azure_endpoint
if [ ! -z "$azure_endpoint" ]; then
    sed -i.bak "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$azure_endpoint|" .env
fi

read -p "Azure OpenAI API Key: " azure_key
if [ ! -z "$azure_key" ]; then
    sed -i.bak "s|AZURE_OPENAI_API_KEY=.*|AZURE_OPENAI_API_KEY=$azure_key|" .env
fi

# OpenAI
read -p "OpenAI API Key (如果不使用 Azure): " openai_key
if [ ! -z "$openai_key" ]; then
    sed -i.bak "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$openai_key|" .env
fi

# 資料庫路徑
read -p "資料庫根目錄 [PosTest]: " db_root
db_root=${db_root:-PosTest}
sed -i.bak "s|DB_ROOT_DIRECTORY=.*|DB_ROOT_DIRECTORY=$db_root|" .env

# 清理備份檔案
rm -f .env.bak

echo ""
echo "========================================"
echo "  ✅ 設置完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 驗證配置："
echo "   python src/config.py"
echo ""
echo "2. 安裝依賴（如果還沒安裝）："
echo "   pip install python-dotenv"
echo ""
echo "3. 開始使用："
echo "   python test_query_interface.py"
echo ""
