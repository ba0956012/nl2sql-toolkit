"""
配置管理模組
從 .env 檔案或環境變數讀取配置
"""
import os
from pathlib import Path
from typing import Optional

# 嘗試載入 python-dotenv
try:
    from dotenv import load_dotenv
    # 載入 .env 檔案
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 已載入配置: {env_path}")
    else:
        print(f"⚠️  未找到 .env 檔案: {env_path}")
        print("   將使用環境變數或預設值")
except ImportError:
    print("⚠️  未安裝 python-dotenv，將使用環境變數")
    print("   安裝方式: pip install python-dotenv")


class Config:
    """配置類別"""
    
    # ============================================
    # Azure OpenAI 配置
    # ============================================
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    
    # ============================================
    # OpenAI 配置
    # ============================================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1/chat/completions")
    
    # ============================================
    # 預設模型
    # ============================================
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    
    # ============================================
    # 資料庫路徑配置
    # ============================================
    DB_ROOT_DIRECTORY: str = os.getenv("DB_ROOT_DIRECTORY", "PosTest")
    DB_MODE: str = os.getenv("DB_MODE", "dev")
    
    # ============================================
    # Few-shot 配置
    # ============================================
    FEWSHOT_EXAMPLES_COUNT: int = int(os.getenv("FEWSHOT_EXAMPLES_COUNT", "5"))
    
    # ============================================
    # Pipeline 配置
    # ============================================
    PIPELINE_NODES: str = os.getenv(
        "PIPELINE_NODES",
        "generate_db_schema+extract_col_value+extract_query_noun+column_retrieve_and_other_info+candidate_generate+align_correct+vote"
    )
    
    # ============================================
    # Embedding 配置
    # ============================================
    BERT_MODEL: str = os.getenv("BERT_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    
    # ============================================
    # Web 界面配置
    # ============================================
    WEB_PORT: int = int(os.getenv("WEB_PORT", "5002"))
    FEWSHOT_PORT: int = int(os.getenv("FEWSHOT_PORT", "5003"))
    
    # ============================================
    # Docker 配置
    # ============================================
    DOCKER_SERVICE_NAME: str = os.getenv("DOCKER_SERVICE_NAME", "opensearch-sql-web")
    DOCKER_WEB_PORT: int = int(os.getenv("DOCKER_WEB_PORT", "5002"))
    DOCKER_FEWSHOT_PORT: int = int(os.getenv("DOCKER_FEWSHOT_PORT", "5003"))
    
    # ============================================
    # 日誌配置
    # ============================================
    LOG_DIRECTORY: str = os.getenv("LOG_DIRECTORY", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ============================================
    # Debug 配置
    # ============================================
    DEBUG_PRINT_PROMPT: bool = os.getenv("DEBUG_PRINT_PROMPT", "false").lower() in ("true", "1", "yes")
    
    # ============================================
    # DeepSeek 配置
    # ============================================
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/chat/completions")
    
    # ============================================
    # Qwen 配置
    # ============================================
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    
    # ============================================
    # 其他配置
    # ============================================
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))
    TOP_P: float = float(os.getenv("TOP_P", "1.0"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "800"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "50"))
    
    @classmethod
    def get_azure_config(cls) -> dict:
        """獲取 Azure OpenAI 配置"""
        return {
            "endpoint": cls.AZURE_OPENAI_ENDPOINT,
            "api_key": cls.AZURE_OPENAI_API_KEY
        }
    
    @classmethod
    def get_openai_config(cls) -> dict:
        """獲取 OpenAI 配置"""
        return {
            "api_key": cls.OPENAI_API_KEY,
            "api_base": cls.OPENAI_API_BASE
        }
    
    @classmethod
    def is_azure_configured(cls) -> bool:
        """檢查是否配置了 Azure OpenAI"""
        return bool(cls.AZURE_OPENAI_ENDPOINT and cls.AZURE_OPENAI_API_KEY)
    
    @classmethod
    def is_openai_configured(cls) -> bool:
        """檢查是否配置了 OpenAI"""
        return bool(cls.OPENAI_API_KEY)
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        驗證配置
        
        Returns:
            (is_valid, errors): 是否有效和錯誤訊息列表
        """
        errors = []
        
        # 檢查至少有一個 API 配置
        if not cls.is_azure_configured() and not cls.is_openai_configured():
            errors.append("未配置 Azure OpenAI 或 OpenAI API")
            errors.append("請在 .env 檔案中設定 AZURE_OPENAI_* 或 OPENAI_API_KEY")
        
        return len(errors) == 0, errors
    
    @classmethod
    def print_config(cls):
        """列印當前配置（隱藏敏感資訊）"""
        print("\n" + "=" * 60)
        print("當前配置")
        print("=" * 60)
        
        def mask_secret(value: str) -> str:
            """遮蔽敏感資訊"""
            if not value or len(value) < 8:
                return "***"
            return value[:4] + "***" + value[-4:]
        
        print(f"\n🔑 API 配置:")
        if cls.is_azure_configured():
            print(f"  ✅ Azure OpenAI: {mask_secret(cls.AZURE_OPENAI_API_KEY)}")
            print(f"     Endpoint: {cls.AZURE_OPENAI_ENDPOINT[:50]}...")
        else:
            print(f"  ❌ Azure OpenAI: 未配置")
        
        if cls.is_openai_configured():
            print(f"  ✅ OpenAI: {mask_secret(cls.OPENAI_API_KEY)}")
        else:
            print(f"  ❌ OpenAI: 未配置")
        
        print(f"\n🤖 模型配置:")
        print(f"  預設模型: {cls.DEFAULT_MODEL}")
        print(f"  溫度: {cls.TEMPERATURE}")
        print(f"  Top P: {cls.TOP_P}")
        print(f"  最大 Token: {cls.MAX_TOKENS}")
        
        print(f"\n📁 路徑配置:")
        print(f"  資料庫根目錄: {cls.DB_ROOT_DIRECTORY}")
        print(f"  資料庫模式: {cls.DB_MODE}")
        print(f"  日誌目錄: {cls.LOG_DIRECTORY}")
        
        print(f"\n🌐 Web 配置:")
        print(f"  Web 端口: {cls.WEB_PORT}")
        print(f"  Few-shot 端口: {cls.FEWSHOT_PORT}")
        
        print(f"\n🔧 其他配置:")
        print(f"  BERT 模型: {cls.BERT_MODEL}")
        print(f"  Embedding 設備: {cls.EMBEDDING_DEVICE}")
        print(f"  Few-shot 範例數: {cls.FEWSHOT_EXAMPLES_COUNT}")
        
        print("=" * 60 + "\n")


# 全域配置實例
config = Config()

# 驗證配置
is_valid, errors = config.validate()
if not is_valid:
    print("\n⚠️  配置驗證失敗:")
    for error in errors:
        print(f"  - {error}")
    print()


if __name__ == "__main__":
    # 測試配置
    config.print_config()
    
    # 驗證配置
    is_valid, errors = config.validate()
    if is_valid:
        print("✅ 配置驗證通過")
    else:
        print("❌ 配置驗證失敗:")
        for error in errors:
            print(f"  - {error}")
