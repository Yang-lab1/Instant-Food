"""
拍立食 - Supabase 客户端
"""
from __future__ import annotations

import mimetypes
import logging
from typing import Any, Dict, Optional
import uuid

from supabase import Client, create_client

from config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client singleton."""

    _instance: Optional[Client] = None
    _admin_client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            cls._instance = create_client(settings.supabase_url, settings.supabase_anon_key)
            logger.info("Supabase client initialized")
        return cls._instance

    @classmethod
    def get_admin_client(cls) -> Client:
        if cls._admin_client is None:
            cls._admin_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            logger.info("Supabase admin client initialized")
        return cls._admin_client

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._admin_client = None
        logger.info("Supabase clients reset")


def get_supabase() -> Client:
    return SupabaseClient.get_client()


def get_supabase_admin() -> Client:
    return SupabaseClient.get_admin_client()


def upload_generated_image(
    image_bytes: bytes,
    *,
    content_type: str = "image/png",
    prefix: str = "generated",
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload a generated image and return its storage metadata."""
    client = get_supabase_admin()
    extension = mimetypes.guess_extension(content_type) or ".png"
    object_name = filename or f"{uuid.uuid4().hex}{extension}"
    path = f"{prefix.rstrip('/')}/{object_name}"
    bucket = client.storage.from_(settings.storage_bucket)

    bucket.upload(
        path=path,
        file=image_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )

    public_url = bucket.get_public_url(path)
    if isinstance(public_url, dict):
        public_url = (
            public_url.get("publicURL")
            or public_url.get("publicUrl")
            or public_url.get("signedURL")
            or public_url.get("signedUrl")
        )

    signed_url = None
    if not public_url:
        signed = bucket.create_signed_url(path, 60 * 60 * 24 * 7)
        if isinstance(signed, dict):
            signed_url = signed.get("signedURL") or signed.get("signedUrl")

    return {
        "path": path,
        "public_url": public_url,
        "signed_url": signed_url,
        "url": public_url or signed_url,
    }
