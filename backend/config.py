"""
拍立食 - 拍立食后端配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # Supabase 配置
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # AI API 配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # AI 模型配置
    ai_model: str = "gpt-4o"
    vision_model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # 应用配置
    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False
    
    # API 配置
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # 图片配置
    max_image_size_mb: int = 10
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # 存储配置
    use_supabase_storage: bool = True
    storage_bucket: str = "recipe-images"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
    
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)
    
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)


# 全局配置实例
settings = Settings()
