import os
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Literal
from dotenv import load_dotenv

# 手动加载.env文件
load_dotenv()


class Settings(BaseSettings):
    """全局配置设置"""
    # 应用设置
    APP_NAME: str = "材料领域翻译质量评估系统API"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 数据路径设置
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "data")
    TERMINOLOGY_DIR: str = os.path.join(DATA_DIR, "terminology")
    TRANSLATION_EXAMPLES_DIR: str = os.path.join(DATA_DIR, "examples")
    REFERENCE_TEXTS_DIR: str = os.path.join(DATA_DIR, "references")
    
    # 数据库设置
    DATABASE_PATH: str = os.path.join(DATA_DIR, "terminology.db")
    
    # 语言模型设置
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", "")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "")
    LLM_API_BASE_URL: str = os.getenv("LLM_API_BASE_URL", "")
    
    # 自定义API设置（与OpenAI API兼容）
    CUSTOM_API_ENABLED: bool = os.getenv("CUSTOM_API_ENABLED", "").lower() in ["true", "1", "yes", "y", "t"]
    CUSTOM_API_KEY: Optional[str] = os.getenv("CUSTOM_API_KEY", "")
    CUSTOM_API_BASE_URL: str = os.getenv("CUSTOM_API_BASE_URL", "")
    CUSTOM_API_VERSION: str = os.getenv("CUSTOM_API_VERSION", "")
    
    # 评估设置
    BLEU_WEIGHT: float = float(os.getenv("BLEU_WEIGHT", "0.4"))
    TERMINOLOGY_WEIGHT: float = float(os.getenv("TERMINOLOGY_WEIGHT", "0.2"))
    SENTENCE_STRUCTURE_WEIGHT: float = float(os.getenv("SENTENCE_STRUCTURE_WEIGHT", "0.2"))
    DISCOURSE_WEIGHT: float = float(os.getenv("DISCOURSE_WEIGHT", "0.2"))
    
    # 术语评估模式: "database" 使用术语库, "reference" 使用参考文本中的术语, "ai_extraction" 使用AI提取
    TERMINOLOGY_EVALUATION_MODE: str = os.getenv("TERMINOLOGY_EVALUATION_MODE", "database")
    
    # 是否在前端加载默认的API配置
    LOAD_DEFAULT_API_CONFIG: bool = os.getenv("LOAD_DEFAULT_API_CONFIG", "True").lower() == "true"
    
    @property
    def EVALUATION_WEIGHTS(self) -> Dict[str, float]:
        """获取评估权重"""
        return {
            "bleu": self.BLEU_WEIGHT,
            "terminology": self.TERMINOLOGY_WEIGHT,
            "sentence_structure": self.SENTENCE_STRUCTURE_WEIGHT,
            "discourse": self.DISCOURSE_WEIGHT
        }
    
    # CORS设置
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
        "*"
    ]
    
    model_config = {
        "env_file": ".env"
    }


settings = Settings()
