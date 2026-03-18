"""
FastAPI 配置文件
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    api_title: str = "AI Chat API"
    api_version: str = "1.0.0"

    # 模型配置
    dashscope_api_key: str = ""
    model_name: str = "qwen-turbo"
    temperature: float = 0.1

    # CORS 配置
    cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
