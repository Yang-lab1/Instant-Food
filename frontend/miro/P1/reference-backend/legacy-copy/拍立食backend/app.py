"""
香疯了 / 拍立食 - FastAPI 后端主入口
====================================

启动命令（开发）：uvicorn app:app --reload --port 8000
启动命令（生产）：uvicorn app:app --host 0.0.0.0 --port 8000

访问 http://localhost:8000/docs 查看自动生成的 API 文档
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from services.rag_retriever import RAGRetriever
from services.normality_scorer import NormalityScorer
from services.image_recognition import ImageRecognizer
from services.llm_generator import LLMGenerator


load_dotenv()


# ============================================================
# 全局单例：启动时加载一次，所有请求共用
# ============================================================

retriever = RAGRetriever()
scorer = NormalityScorer()
recognizer = ImageRecognizer()
generator = LLMGenerator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期：启动时加载模型和索引"""
    # 启动
    retriever.load(
        index_path="models/recipes.index",
        meta_path="models/recipes_meta.json",
    )
    scorer.load(
        clf_path="models/normality_clf.joblib",
        vec_path="models/normality_vec.joblib",
    )
    recognizer.init()
    generator.init()

    print("🚀 所有服务加载完成，开始接客")

    # 把单例挂到 app.state 上，路由里通过 request.app.state 访问
    app.state.retriever = retriever
    app.state.scorer = scorer
    app.state.recognizer = recognizer
    app.state.generator = generator

    yield

    # 关闭（如果需要清理资源）
    print("👋 服务关闭")


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="香疯了 / 拍立食 API",
    description="拍冰箱 → 识别食材 → 香了(RAG) or 疯了(LLM) → 正常度打分",
    version="0.1.0",
    lifespan=lifespan,
)

# 允许小程序跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改成你的域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health():
    return {"status": "ok", "message": "香疯了后端运行中 🍳"}


# ============================================================
# 数据模型
# ============================================================

from pydantic import BaseModel
from fastapi import UploadFile, File, HTTPException
import base64


class IngredientsRequest(BaseModel):
    ingredients: list[str]
    route: str  # "香了" 或 "疯了"


class FallbackRequest(BaseModel):
    ingredients: list[str]


# ============================================================
# API 端点
# ============================================================

@app.post("/api/recognize")
async def recognize_ingredients(image: UploadFile = File(...)):
    """上传冰箱照片 → 返回识别出的食材列表"""
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    content_type = image.content_type or "image/jpeg"

    try:
        ingredients = await recognizer.recognize(image_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识图失败: {str(e)}")

    return {
        "ingredients": ingredients,
        "message": f"识别到 {len(ingredients)} 种食材",
    }


@app.post("/api/recipe")
async def get_recipe(request: IngredientsRequest):
    """根据食材和路线，返回菜谱 + 正常度分数"""
    ingredients = request.ingredients
    route = request.route

    if not ingredients:
        raise HTTPException(status_code=400, detail="食材列表不能为空")

    if route == "香了":
        results = retriever.search(ingredients, top_k=5)
        recipes_with_score = []
        for r in results:
            ing_names = [ing["name"] for ing in r["ingredients"]]
            sea_names = [s["name"] for s in r.get("seasonings", [])]
            score_result = scorer.score_recipe(ing_names, sea_names)
            recipes_with_score.append({
                "dish_name": r["dish_name"],
                "ingredients": r["ingredients"],
                "seasonings": r.get("seasonings", []),
                "steps": r.get("steps", []),
                "brief_intro": r.get("brief_intro", ""),
                "normality_score": score_result["normality_score"],
                "normality_label": score_result["label"],
            })
        return {
            "route": "香了",
            "recipes": recipes_with_score,
            "message": "稳健推荐，安全靠谱 🍳",
        }

    elif route == "疯了":
        try:
            generated = await generator.generate(ingredients)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM 生成失败: {str(e)}")

        score_result = scorer.score_recipe(
            generated.get("ingredients", []),
            generated.get("seasonings", []),
            verbose=True,
        )
        return {
            "route": "疯了",
            "recipe": generated,
            "normality_score": score_result["normality_score"],
            "normality_label": score_result["label"],
            "reasons": score_result.get("reasons", []),
            "can_fallback": True,
            "message": f"正常度：{score_result['normality_score']}%",
        }

    else:
        raise HTTPException(status_code=400, detail="路线必须是 '香了' 或 '疯了'")


@app.post("/api/fallback")
async def fallback_to_rag(request: FallbackRequest):
    """疯了路线的 RAG 兜底"""
    results = retriever.search(request.ingredients, top_k=5)
    recipes_with_score = []
    for r in results:
        ing_names = [ing["name"] for ing in r["ingredients"]]
        sea_names = [s["name"] for s in r.get("seasonings", [])]
        score_result = scorer.score_recipe(ing_names, sea_names)
        recipes_with_score.append({
            "dish_name": r["dish_name"],
            "ingredients": r["ingredients"],
            "seasonings": r.get("seasonings", []),
            "steps": r.get("steps", []),
            "brief_intro": r.get("brief_intro", ""),
            "normality_score": score_result["normality_score"],
            "normality_label": score_result["label"],
        })
    return {
        "route": "兜底",
        "recipes": recipes_with_score,
        "message": "没关系，安全菜谱来了 🛟",
    }
