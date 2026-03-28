"""
拍立食 - API 路由
"""
import base64
import logging
from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from database.supabase_client import get_supabase, get_supabase_admin
from api.ai_client import get_ai_client, AIServiceError

logger = logging.getLogger(__name__)

# ============================================
# Pydantic 模型
# ============================================

class IngredientInput(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = "g"
    notes: Optional[str] = None


class RecipeGenerateRequest(BaseModel):
    ingredients: List[str]
    cooking_technique: str = "炒"
    flavor_profile: str = "川菜"
    spice_level: int = Field(default=3, ge=1, le=5)
    max_time: int = Field(default=30, ge=5, le=180)
    equipment: Optional[List[str]] = None


class ImageRecognizeRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class UserPreferencesRequest(BaseModel):
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    preferred_cuisines: List[str] = []
    disliked_ingredients: List[str] = []
    preferred_spice_level: int = Field(default=3, ge=1, le=5)
    calorie_target: Optional[int] = None
    meal_preferences: List[str] = []
    equipment_available: List[str] = []


class RecipeCreateRequest(BaseModel):
    title: str
    title_zh: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    cuisine_type: Optional[str] = None
    meal_type: Optional[str] = None
    difficulty: str = "medium"
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    servings: int = 1
    calories_per_serving: Optional[int] = None
    image_url: Optional[str] = None
    ingredients: List[IngredientInput] = []
    steps: List[dict] = []
    is_published: bool = False
    source: str = "manual"


# ============================================
# API 路由
# ============================================

router = APIRouter()


# 健康检查
@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "instant-food-backend"
    }


# AI 服务状态
@router.get("/ai/status")
async def ai_status():
    """AI 服务状态"""
    ai = get_ai_client()
    return {
        "available": ai.is_available,
        "provider": ai.provider_name,
        "model": ai.model_name
    }


# ============================================
# AI 生成 API
# ============================================

@router.post("/generate/from-image")
async def generate_from_image(request: ImageRecognizeRequest):
    """
    从图片识别食材并生成食谱
    """
    ai = get_ai_client()
    
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        # 步骤1: 识别图片中的食材
        if request.image_base64:
            image_data = base64.b64decode(request.image_base64)
            recognition_result = ai.recognize_image(image_data)
        elif request.image_url:
            recognition_result = ai.recognize_image_from_url(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")
        
        # 提取识别的食材名称
        ingredient_names = [i["name"] for i in recognition_result.ingredients]
        
        # 步骤2: 生成食谱
        recipe_result = ai.generate_recipe(
            ingredients=ingredient_names,
            cooking_technique=recognition_result.cooking_method
        )
        
        # 记录到数据库
        try:
            supabase = get_supabase_admin()
            supabase.table("generation_logs").insert({
                "recognized_ingredients": ingredient_names,
                "generated_recipe": recipe_result.to_dict(),
                "ai_model_used": ai.model_name,
                "quality_rating": None,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to log generation: {e}")
        
        return {
            "success": True,
            "recognition": recognition_result.to_dict(),
            "recipe": recipe_result.to_dict()
        }
        
    except AIServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/recipe")
async def generate_recipe(request: RecipeGenerateRequest):
    """
    根据食材和偏好生成食谱
    """
    ai = get_ai_client()
    
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        recipe_result = ai.generate_recipe(
            ingredients=request.ingredients,
            cooking_technique=request.cooking_technique,
            flavor_profile=request.flavor_profile,
            spice_level=request.spice_level,
            max_time=request.max_time,
            equipment=request.equipment
        )
        
        return {
            "success": True,
            "recipe": recipe_result.to_dict()
        }
        
    except AIServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recognize/image")
async def recognize_image(request: ImageRecognizeRequest):
    """
    识别图片中的食材
    """
    ai = get_ai_client()
    
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        if request.image_base64:
            image_data = base64.b64decode(request.image_base64)
            result = ai.recognize_image(image_data)
        elif request.image_url:
            result = ai.recognize_image_from_url(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")
        
        return {
            "success": True,
            "result": result.to_dict()
        }
        
    except AIServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 食谱管理 API
# ============================================

@router.post("/recipes")
async def create_recipe(request: RecipeCreateRequest):
    """
    创建食谱
    """
    try:
        supabase = get_supabase_admin()
        
        # 插入食谱主表
        recipe_data = {
            "title": request.title,
            "title_zh": request.title_zh or request.title,
            "description": request.description,
            "description_zh": request.description_zh or request.description,
            "cuisine_type": request.cuisine_type,
            "meal_type": request.meal_type,
            "difficulty": request.difficulty,
            "prep_time_minutes": request.prep_time_minutes,
            "cook_time_minutes": request.cook_time_minutes,
            "servings": request.servings,
            "calories_per_serving": request.calories_per_serving,
            "image_url": request.image_url,
            "is_published": request.is_published,
            "source": request.source,
            "is_ai_generated": request.source == "ai_generated"
        }
        
        recipe_response = supabase.table("recipes").insert(recipe_data).execute()
        recipe = recipe_response.data[0] if recipe_response.data else None
        
        if not recipe:
            raise HTTPException(status_code=500, detail="Failed to create recipe")
        
        # 插入食材关联
        for idx, ing in enumerate(request.ingredients):
            supabase.table("recipe_ingredients").insert({
                "recipe_id": recipe["id"],
                "ingredient_name": ing.name,
                "quantity": ing.quantity,
                "unit": ing.unit,
                "notes": ing.notes,
                "sort_order": idx
            }).execute()
        
        # 插入步骤
        for idx, step in enumerate(request.steps):
            supabase.table("recipe_steps").insert({
                "recipe_id": recipe["id"],
                "step_number": idx + 1,
                "instruction": step.get("instruction", ""),
                "instruction_zh": step.get("instruction_zh"),
                "duration_minutes": step.get("duration_minutes"),
                "tips": step.get("tips")
            }).execute()
        
        return {
            "success": True,
            "recipe": recipe
        }
        
    except Exception as e:
        logger.error(f"Create recipe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipes")
async def list_recipes(
    limit: int = 20,
    offset: int = 0,
    cuisine_type: Optional[str] = None,
    meal_type: Optional[str] = None,
    published_only: bool = True
):
    """
    获取食谱列表
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("recipes").select("*")
        
        if published_only:
            query = query.eq("is_published", True)
        
        if cuisine_type:
            query = query.eq("cuisine_type", cuisine_type)
        
        if meal_type:
            query = query.eq("meal_type", meal_type)
        
        response = query.range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "recipes": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        logger.error(f"List recipes failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """
    获取单个食谱详情
    """
    try:
        supabase = get_supabase()
        
        # 获取食谱
        recipe_response = supabase.table("recipes").select("*").eq("id", recipe_id).execute()
        
        if not recipe_response.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        recipe = recipe_response.data[0]
        
        # 获取食材
        ingredients_response = supabase.table("recipe_ingredients").select("*").eq("recipe_id", recipe_id).order("sort_order").execute()
        
        # 获取步骤
        steps_response = supabase.table("recipe_steps").select("*").eq("recipe_id", recipe_id).order("step_number").execute()
        
        recipe["ingredients"] = ingredients_response.data
        recipe["steps"] = steps_response.data
        
        return {
            "success": True,
            "recipe": recipe
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get recipe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str):
    """
    删除食谱
    """
    try:
        supabase = get_supabase_admin()
        supabase.table("recipes").delete().eq("id", recipe_id).execute()
        
        return {"success": True, "message": "Recipe deleted"}
        
    except Exception as e:
        logger.error(f"Delete recipe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 食材管理 API
# ============================================

@router.get("/ingredients")
async def list_ingredients(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None
):
    """
    获取食材列表
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("ingredients").select("*")
        
        if category:
            query = query.eq("category", category)
        
        response = query.range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "ingredients": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        logger.error(f"List ingredients failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ingredients/search")
async def search_ingredients(q: str, limit: int = 20):
    """
    搜索食材
    """
    try:
        supabase = get_supabase()
        
        # 使用 ILIKE 进行模糊搜索
        response = supabase.table("ingredients").select("*").or_(
            f"name.ilike.%{q}%,name_zh.ilike.%{q}%"
        ).limit(limit).execute()
        
        return {
            "success": True,
            "ingredients": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        logger.error(f"Search ingredients failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 风味档案 & 烹饪技法 API
# ============================================

@router.get("/flavor-profiles")
async def list_flavor_profiles():
    """获取风味档案列表"""
    try:
        supabase = get_supabase()
        response = supabase.table("flavor_profiles").select("*").execute()
        
        return {
            "success": True,
            "profiles": response.data
        }
    except Exception as e:
        logger.error(f"List flavor profiles failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cooking-techniques")
async def list_cooking_techniques():
    """获取烹饪技法列表"""
    try:
        supabase = get_supabase()
        response = supabase.table("cooking_techniques").select("*").execute()
        
        return {
            "success": True,
            "techniques": response.data
        }
    except Exception as e:
        logger.error(f"List cooking techniques failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 用户偏好 API
# ============================================

@router.post("/user/preferences")
async def save_user_preferences(user_id: str, request: UserPreferencesRequest):
    """保存用户偏好"""
    try:
        supabase = get_supabase_admin()
        
        preferences_data = {
            "user_id": user_id,
            "dietary_restrictions": request.dietary_restrictions,
            "allergies": request.allergies,
            "preferred_cuisines": request.preferred_cuisines,
            "disliked_ingredients": request.disliked_ingredients,
            "preferred_spice_level": request.preferred_spice_level,
            "calorie_target": request.calorie_target,
            "meal_preferences": request.meal_preferences,
            "equipment_available": request.equipment_available,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # 使用 upsert
        supabase.table("user_preferences").upsert(preferences_data, on_conflict="user_id").execute()
        
        return {"success": True, "message": "Preferences saved"}
        
    except Exception as e:
        logger.error(f"Save preferences failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """获取用户偏好"""
    try:
        supabase = get_supabase()
        response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            # 返回默认偏好
            return {
                "success": True,
                "preferences": {
                    "user_id": user_id,
                    "dietary_restrictions": [],
                    "allergies": [],
                    "preferred_cuisines": [],
                    "disliked_ingredients": [],
                    "preferred_spice_level": 3,
                    "meal_preferences": [],
                    "equipment_available": ["炒锅", "砧板", "菜刀"]
                }
            }
        
        return {
            "success": True,
            "preferences": response.data[0]
        }
        
    except Exception as e:
        logger.error(f"Get preferences failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 生成日志 API
# ============================================

@router.post("/generation/log")
async def log_generation(
    user_id: Optional[str] = None,
    recognized_ingredients: List[str] = [],
    generated_recipe: dict = {},
    ai_model_used: str = "gpt-4o",
    quality_rating: Optional[int] = None
):
    """记录生成日志"""
    try:
        supabase = get_supabase_admin()
        
        log_data = {
            "user_id": user_id,
            "recognized_ingredients": recognized_ingredients,
            "generated_recipe": generated_recipe,
            "ai_model_used": ai_model_used,
            "quality_rating": quality_rating,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("generation_logs").insert(log_data).execute()
        
        return {
            "success": True,
            "log_id": response.data[0]["id"] if response.data else None
        }
        
    except Exception as e:
        logger.error(f"Log generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/export")
async def export_training_data(limit: int = 1000):
    """导出 AI 训练数据"""
    try:
        supabase = get_supabase_admin()
        
        response = supabase.table("generation_logs").select("*").eq("quality_rating", 4).gte("quality_rating", 4).limit(limit).execute()
        
        # 转换为训练数据格式
        training_data = []
        for log in response.data:
            training_data.append({
                "input": f"食材: {', '.join(log.get('recognized_ingredients', []))}",
                "output": log.get("generated_recipe", {}),
                "quality_rating": log.get("quality_rating")
            })
        
        return {
            "success": True,
            "count": len(training_data),
            "data": training_data
        }
        
    except Exception as e:
        logger.error(f"Export training data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 档案馆 API
# ============================================

@router.get("/archives")
async def list_archives(user_id: Optional[str] = None, limit: int = 20, offset: int = 0):
    """获取档案列表"""
    try:
        supabase = get_supabase()
        
        query = supabase.table("archives").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        response = query.range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "archives": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        logger.error(f"List archives failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archives")
async def create_archive(
    user_id: str,
    title: str,
    recipe_id: Optional[str] = None,
    generation_log_id: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    is_shared: bool = False
):
    """创建档案"""
    try:
        supabase = get_supabase_admin()
        
        archive_data = {
            "user_id": user_id,
            "title": title,
            "recipe_id": recipe_id,
            "generation_log_id": generation_log_id,
            "cover_image_url": cover_image_url,
            "is_shared": is_shared,
            "shared_at": datetime.utcnow().isoformat() if is_shared else None
        }
        
        response = supabase.table("archives").insert(archive_data).execute()
        
        return {
            "success": True,
            "archive": response.data[0] if response.data else None
        }
        
    except Exception as e:
        logger.error(f"Create archive failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 初始化 __init__.py
# ============================================
