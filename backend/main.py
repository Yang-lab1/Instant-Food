"""
拍立食 - FastAPI 主应用
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import router
from api.ai_client import get_ai_client

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    ai = get_ai_client()

    # 启动时
    logger.info("拍立食后端服务启动中...")
    logger.info(f"环境: {settings.app_env}")
    logger.info(f"AI 服务: {ai.provider_name}")
    
    yield
    
    # 关闭时
    logger.info("拍立食后端服务关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title="拍立食 API",
    description="拍立食食谱生成与食材识别后端服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.api_prefix)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "拍立食后端",
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
