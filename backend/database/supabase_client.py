"""
拍立食 - Supabase 数据库客户端
"""
from supabase import create_client, Client
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase 客户端单例"""
    
    _instance: Optional[Client] = None
    _admin_client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """获取普通客户端 (使用 anon key)"""
        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            logger.info("Supabase client initialized")
        return cls._instance
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """获取管理员客户端 (使用 service role key)"""
        if cls._admin_client is None:
            cls._admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            logger.info("Supabase admin client initialized")
        return cls._admin_client
    
    @classmethod
    def reset(cls):
        """重置客户端连接"""
        cls._instance = None
        cls._admin_client = None
        logger.info("Supabase clients reset")


# 便捷访问函数
def get_supabase() -> Client:
    """获取 Supabase 客户端"""
    return SupabaseClient.get_client()


def get_supabase_admin() -> Client:
    """获取 Supabase 管理员客户端"""
    return SupabaseClient.get_admin_client()
