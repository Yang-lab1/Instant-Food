"""Application settings for the Instant Food backend."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    ai_model: str = "gemini-2.5-flash"
    vision_model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.5-flash-image"
    max_tokens: int = 4096
    temperature: float = 0.7

    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    api_prefix: str = "/api/v1"
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    max_image_size_mb: int = 10
    allowed_image_types_raw: str = Field(
        default="image/jpeg,image/png,image/webp",
        alias="ALLOWED_IMAGE_TYPES",
    )

    use_supabase_storage: bool = True
    storage_bucket: str = "recipe-images"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origins(self) -> List[str]:
        return _split_csv(self.cors_origins_raw)

    @property
    def allowed_image_types(self) -> List[str]:
        return _split_csv(self.allowed_image_types_raw)

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

    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def ai_provider(self) -> str:
        if self.has_gemini():
            return "gemini"
        if self.has_openai():
            return "openai"
        if self.has_anthropic():
            return "anthropic"
        return "none"


settings = Settings()
