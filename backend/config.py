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
    backup_api_key: Optional[str] = Field(default=None, alias="BACKUP_API_KEY")
    backup_api_base_url: str = Field(default="https://api.openai.com/v1", alias="BACKUP_API_BASE_URL")
    backup_text_model: Optional[str] = Field(default=None, alias="BACKUP_TEXT_MODEL")
    backup_image_model: Optional[str] = Field(default=None, alias="BACKUP_IMAGE_MODEL")
    backup_provider_name: str = Field(default="openai_compatible", alias="BACKUP_PROVIDER")
    backup_timeout_connect_seconds: float = Field(default=10.0, alias="BACKUP_TIMEOUT_CONNECT_SECONDS")
    backup_timeout_read_seconds: float = Field(default=45.0, alias="BACKUP_TIMEOUT_READ_SECONDS")
    backup_timeout_write_seconds: float = Field(default=45.0, alias="BACKUP_TIMEOUT_WRITE_SECONDS")
    backup_timeout_pool_seconds: float = Field(default=10.0, alias="BACKUP_TIMEOUT_POOL_SECONDS")
    backup_request_retry_attempts: int = Field(default=2, alias="BACKUP_REQUEST_RETRY_ATTEMPTS")
    image_generation_retry_attempts: int = Field(default=2, alias="IMAGE_GENERATION_RETRY_ATTEMPTS")

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
    cors_origin_regex: Optional[str] = Field(
        default=r"^https://frontend(?:-[a-z0-9-]+)?(?:-yangs-projects-d2ad4c9e)?\.vercel\.app$|^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$",
        alias="CORS_ORIGIN_REGEX",
    )

    max_image_size_mb: int = 10
    allowed_image_types_raw: str = Field(
        default="image/jpeg,image/png,image/webp",
        alias="ALLOWED_IMAGE_TYPES",
    )

    use_supabase_storage: bool = True
    storage_bucket: str = "recipe-images"

    enable_traditional_normality: bool = Field(
        default=True,
        alias="ENABLE_TRADITIONAL_NORMALITY",
    )
    normality_clf_path: str = Field(
        default="models/normality_clf.joblib",
        alias="NORMALITY_CLF_PATH",
    )
    normality_vec_path: str = Field(
        default="models/normality_vec.joblib",
        alias="NORMALITY_VEC_PATH",
    )

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

    def has_backup_api(self) -> bool:
        return bool(self.backup_api_key and self.backup_api_base_url.strip())

    def has_backup_text_model(self) -> bool:
        return bool(self.has_backup_api() and self.backup_text_model and self.backup_text_model.strip())

    def has_backup_image_model(self) -> bool:
        return bool(self.has_backup_api() and self.backup_image_model and self.backup_image_model.strip())

    @property
    def ai_provider(self) -> str:
        if self.has_gemini():
            if self.has_backup_text_model():
                return "gemini+backup"
            return "gemini"
        if self.has_backup_text_model():
            return "backup"
        if self.has_openai():
            return "openai"
        if self.has_anthropic():
            return "anthropic"
        return "none"


settings = Settings()
