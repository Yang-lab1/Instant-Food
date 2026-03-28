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
from config import settings

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


class DishImageGenerateRequest(BaseModel):
    prompt: Optional[str] = None
    recipe_title: Optional[str] = None
    recipe_description: Optional[str] = None
    ingredients: List[str] = []
    generation_log_id: Optional[str] = None


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
    generation_log_id: Optional[str] = None


# ============================================
# API 路由
# ============================================

router = APIRouter()


def upload_generated_image_to_storage(image_base64: str, mime_type: str, prefix: str = "generated") -> str:
    """把生成图片上传到 Supabase Storage，并返回公开 URL。"""
    if not settings.use_supabase_storage:
        raise ValueError("Supabase Storage is disabled")

    extension_map = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
    }
    extension = extension_map.get(mime_type, "png")
    image_bytes = base64.b64decode(image_base64)
    object_path = (
        f"{prefix}/"
        f"{datetime.utcnow().strftime('%Y/%m/%d')}/"
        f"{uuid.uuid4().hex}.{extension}"
    )

    supabase = get_supabase_admin()
    supabase.storage.from_(settings.storage_bucket).upload(
        object_path,
        image_bytes,
        {"content-type": mime_type, "upsert": "true"},
    )
    return supabase.storage.from_(settings.storage_bucket).get_public_url(object_path)


def build_ingredient_atlas(recognition_result, recipe_result):
    atlas = []
    recognition_map = {
        item.get("name"): item for item in (recognition_result.ingredients or [])
    }

    for index, ingredient in enumerate(recipe_result.ingredients or []):
        name = ingredient.get("name") or f"食材 {index + 1}"
        recognized = recognition_map.get(name, {})
        quantity = ingredient.get("quantity") or ingredient.get("estimated_quantity") or "适量"
        unit = ingredient.get("unit") or ""
        atlas.append({
            "name": name,
            "amount": f"{quantity}{unit}".strip() or "适量",
            "role": infer_ingredient_role(name, index),
            "action": infer_ingredient_action(name),
            "intro": ingredient.get("notes") or build_ingredient_intro(name, recognized),
            "confidence": recognized.get("confidence")
        })

    return atlas


def build_teaching_steps(recipe_result):
    teaching_steps = []
    for index, step in enumerate(recipe_result.steps or []):
        instruction = step.get("instruction", "")
        teaching_steps.append({
            "step_no": index + 1,
            "title": infer_step_title(instruction, index),
            "instruction": instruction,
            "duration": (
                f"{step.get('duration_minutes')} 分钟"
                if step.get("duration_minutes")
                else "按状态灵活调整"
            ),
            "tip": step.get("tips") or infer_step_tip(instruction, index)
        })
    return teaching_steps


def build_teaching_summary(recognition_result, recipe_result):
    total_minutes = sum(
        int(step.get("duration_minutes") or 0)
        for step in (recipe_result.steps or [])
    )
    ingredient_count = len(recognition_result.ingredients or [])
    step_count = len(recipe_result.steps or [])

    return [
        {
            "label": "原材料",
            "value": f"{ingredient_count} 项已识别" if ingredient_count else "待补充识别"
        },
        {
            "label": "节奏",
            "value": f"{step_count} 步完成一餐" if step_count else "等待步骤生成"
        },
        {
            "label": "时长",
            "value": f"约 {total_minutes} 分钟" if total_minutes > 0 else "按现场火候判断"
        }
    ]


def build_teaching_text(recognition_result, recipe_result):
    ingredient_names = "、".join(
        item.get("name", "")
        for item in (recognition_result.ingredients or [])
        if item.get("name")
    )
    step_count = len(recipe_result.steps or [])
    tips = recipe_result.tips or "建议先备好食材，再按步骤逐步完成。"
    return (
        f"本次识别到的主要原材料有：{ingredient_names or '待补充'}。"
        f"系统共生成 {step_count} 个操作步骤，并整理了食材图谱和教学提示。"
        f"{tips}"
    )


def build_generated_image_urls(request):
    if request.image_url:
        return [request.image_url]
    return []


def build_generation_status_payload(request, recognition_result, recipe_result, ai):
    return {
        "input_image_url": request.image_url,
        "input_image_base64": request.image_base64,
        "recognized_ingredients": [
            item.get("name")
            for item in (recognition_result.ingredients or [])
            if item.get("name")
        ],
        "generated_recipe": recipe_result.to_dict(),
        "ai_model_used": ai.model_name,
        "generated_image_url": request.image_url,
        "generated_image_urls": build_generated_image_urls(request),
        "generated_image_prompt": f"根据上传原材料图片生成菜谱《{recipe_result.title_zh or recipe_result.title}》",
        "ingredient_atlas": build_ingredient_atlas(recognition_result, recipe_result),
        "teaching_steps": build_teaching_steps(recipe_result),
        "teaching_summary": build_teaching_summary(recognition_result, recipe_result),
        "teaching_text": build_teaching_text(recognition_result, recipe_result),
        "generation_type": "image_to_recipe",
        "generation_status": "completed",
        "quality_rating": None,
        "created_at": datetime.utcnow().isoformat()
    }


def build_text_generation_status_payload(request, recipe_result, ai):
    flow_text = " ".join(
        step.get("instruction", "").strip()
        for step in (recipe_result.steps or [])
        if step.get("instruction")
    ).strip()

    ingredient_atlas = []
    for index, name in enumerate(request.ingredients):
        ingredient_atlas.append({
            "name": name,
            "amount": "按输入数量",
            "role": infer_ingredient_role(name, index),
            "action": infer_ingredient_action(name),
            "intro": f"{name}已纳入本次纯文字生成，可按家庭烹饪习惯提前处理。"
        })

    return {
        "recognized_ingredients": request.ingredients,
        "user_preferences": {
            "cooking_technique": request.cooking_technique,
            "flavor_profile": request.flavor_profile,
            "spice_level": request.spice_level,
            "max_time": request.max_time,
            "equipment": request.equipment or [],
        },
        "generated_recipe": recipe_result.to_dict(),
        "ai_model_used": ai.model_name,
        "ingredient_atlas": ingredient_atlas,
        "teaching_steps": build_teaching_steps(recipe_result),
        "teaching_summary": [
            {
                "label": "原材料",
                "value": f"{len(request.ingredients)} 项输入食材"
            },
            {
                "label": "节奏",
                "value": f"{len(recipe_result.steps or [])} 步完成一餐"
            },
            {
                "label": "方式",
                "value": f"{request.cooking_technique} / {request.flavor_profile}"
            }
        ],
        "teaching_text": flow_text or "未从训练库中提取到可用流程说明。",
        "generation_type": "text_to_recipe",
        "generation_status": "completed",
        "quality_rating": None,
        "created_at": datetime.utcnow().isoformat()
    }


def build_ingredient_intro(name, recognized):
    nutrition_notes = recognized.get("estimated_quantity")
    if nutrition_notes:
        return f"{name}在这道菜里建议准备 {nutrition_notes}，下锅前先清洗并处理好。"
    return f"{name}适合提前洗净、切好，正式烹饪时更容易控制节奏。"


def infer_ingredient_role(name, index):
    text_value = name or ""
    if any(token in text_value for token in ["葱", "姜", "蒜", "椒", "香菜"]):
        return "提香点睛"
    if any(token in text_value for token in ["盐", "糖", "酱", "醋", "油", "料酒", "蚝油", "生抽", "老抽"]):
        return "调味关键"
    if any(token in text_value for token in ["蛋", "肉", "鸡", "虾", "鱼", "豆腐"]):
        return "主体蛋白"
    if any(token in text_value for token in ["番茄", "土豆", "青椒", "洋葱", "菌", "白菜", "生菜", "黄瓜"]):
        return "主蔬菜"
    return "核心主料" if index == 0 else "辅助配料"


def infer_ingredient_action(name):
    text_value = name or ""
    if any(token in text_value for token in ["葱", "姜", "蒜", "椒", "洋葱"]):
        return "建议切碎爆香"
    if any(token in text_value for token in ["肉", "鸡", "虾", "鱼"]):
        return "建议提前腌制"
    if "蛋" in text_value:
        return "建议先打散"
    if any(token in text_value for token in ["番茄", "土豆", "黄瓜", "白菜", "豆腐"]):
        return "建议切块备用"
    return "建议洗净备料"


def infer_step_title(instruction, index):
    if any(token in instruction for token in ["洗", "切", "备", "腌"]):
        return "备料阶段"
    if any(token in instruction for token in ["热锅", "下油", "爆香"]):
        return "起锅增香"
    if any(token in instruction for token in ["翻炒", "炒"]):
        return "主火翻炒"
    if any(token in instruction for token in ["煮", "焖", "炖"]):
        return "加热收味"
    if any(token in instruction for token in ["装盘", "出锅"]):
        return "完成装盘"
    return f"步骤 {index + 1}"


def infer_step_tip(instruction, index):
    if any(token in instruction for token in ["洗", "切", "备", "腌"]):
        return "先把全部原材料准备好，正式开火时会更顺手。"
    if any(token in instruction for token in ["热锅", "下油", "爆香"]):
        return "锅热后再下油和香料，更容易把香气带出来。"
    if any(token in instruction for token in ["翻炒", "炒"]):
        return "保持中大火快速翻动，避免局部受热过度。"
    if any(token in instruction for token in ["煮", "焖", "炖"]):
        return "这一步更看重火候和汤汁变化，建议边看边调。"
    if any(token in instruction for token in ["装盘", "出锅"]):
        return "临出锅前试一下味道，再决定是否补调味。"
    if index == 0:
        return "先完成准备动作，后续每一步都会更从容。"
    return "跟着步骤观察状态变化，再决定下一步。"


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
        generation_log_id = None
        try:
            supabase = get_supabase_admin()
            log_payload = build_generation_status_payload(
                request=request,
                recognition_result=recognition_result,
                recipe_result=recipe_result,
                ai=ai
            )
            log_response = supabase.table("generation_logs").insert(log_payload).execute()
            if log_response.data:
                generation_log_id = log_response.data[0].get("id")
        except Exception as e:
            logger.warning(f"Failed to log generation: {e}")
        
        return {
            "success": True,
            "recognition": recognition_result.to_dict(),
            "recipe": recipe_result.to_dict(),
            "generation_log_id": generation_log_id
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

        generation_log_id = None
        try:
            supabase = get_supabase_admin()
            log_payload = build_text_generation_status_payload(
                request=request,
                recipe_result=recipe_result,
                ai=ai
            )
            log_response = supabase.table("generation_logs").insert(log_payload).execute()
            if log_response.data:
                generation_log_id = log_response.data[0].get("id")
        except Exception as e:
            logger.warning(f"Failed to log text generation: {e}")
        
        return {
            "success": True,
            "recipe": recipe_result.to_dict(),
            "generation_log_id": generation_log_id
        }
        
    except AIServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/image")
async def generate_dish_image(request: DishImageGenerateRequest):
    """使用 Gemini 图像模型为已生成菜谱创建示意图。"""
    ai = get_ai_client()

    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")

    prompt = request.prompt or (
        f"请生成一道成品菜图片，菜名是 {request.recipe_title or '家常菜'}。"
        f"描述：{request.recipe_description or '中国家庭厨房风格，摆盘自然，食物真实可口。'}"
        f"主要食材：{', '.join(request.ingredients or [])}。"
        "风格要求：真实食物摄影、暖色灯光、中式家常摆盘、高清细节。"
    )

    try:
        image_result = ai.generate_dish_image(prompt)
        public_image_url = None

        try:
            public_image_url = upload_generated_image_to_storage(
                image_result.image_base64,
                image_result.mime_type,
                prefix="generated-dishes"
            )
        except Exception as e:
            logger.warning(f"Failed to upload generated image to storage: {e}")

        if request.generation_log_id:
            try:
                supabase = get_supabase_admin()
                supabase.table("generation_logs").update({
                    "generated_image_prompt": prompt,
                    "generated_image_url": public_image_url,
                    "generated_image_urls": [public_image_url] if public_image_url else [],
                    "generation_status": "completed"
                }).eq("id", request.generation_log_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update generation log image prompt: {e}")

        return {
            "success": True,
            "image": image_result.to_dict(),
            "image_url": public_image_url,
            "provider": ai.provider_name,
            "model": settings.image_model
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

        if request.generation_log_id:
            supabase.table("generation_logs").update({
                "recipe_id": recipe["id"]
            }).eq("id", request.generation_log_id).execute()
        
        return {
            "success": True,
            "recipe": recipe
        }
    except Exception as e:
        logger.error(f"Create recipe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generation-logs/{log_id}")
async def get_generation_log(log_id: str):
    """获取单条生成日志，用于结果页回显。"""
    try:
        supabase = get_supabase_admin()
        response = (
            supabase.table("generation_logs")
            .select("*")
            .eq("id", log_id)
            .limit(1)
            .execute()
        )
        log_item = response.data[0] if response.data else None
        if not log_item:
            raise HTTPException(status_code=404, detail="Generation log not found")
        return {
            "success": True,
            "log": log_item
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get generation log failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get generation log failed: {str(e)}")


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
