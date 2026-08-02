"""
鎷嶇珛椋?- API 璺敱
"""
from __future__ import annotations

import base64
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.ai_client import AIServiceError, RecipeGenerationResult, get_ai_client
from config import settings
from database.supabase_client import (
    get_supabase,
    get_supabase_admin,
    upload_generated_image,
)
from services.normality_service import get_scorer

logger = logging.getLogger(__name__)
router = APIRouter()


class IngredientInput(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = "g"
    notes: Optional[str] = None


class RecipeGenerateRequest(BaseModel):
    ingredients: List[Any]
    cooking_technique: Optional[str] = None
    technique: Optional[str] = None
    flavor_profile: str = "瀹跺父"
    tastes: List[str] = Field(default_factory=list)
    spice_level: int = Field(default=3, ge=1, le=5)
    max_time: int = Field(default=30, ge=5, le=180)
    equipment: Optional[List[str]] = None
    tools: List[str] = Field(default_factory=list)

    def ingredient_names(self) -> List[str]:
        names: List[str] = []
        for item in self.ingredients:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    names.append(cleaned)
                continue

            if isinstance(item, dict):
                if item.get("included", True) is False:
                    continue
                cleaned = str(item.get("name", "")).strip()
                if cleaned:
                    names.append(cleaned)
                continue

            cleaned = str(getattr(item, "name", "")).strip()
            included = getattr(item, "included", True)
            if cleaned and included is not False:
                names.append(cleaned)

        return names

    def ingredient_details(self) -> List[Dict[str, str]]:
        details: List[Dict[str, str]] = []

        for item in self.ingredients:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    details.append({"name": cleaned, "quantity": "", "unit": ""})
                continue

            if isinstance(item, dict):
                if item.get("included", True) is False:
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                details.append(
                    {
                        "name": name,
                        "quantity": str(item.get("quantity", "")).strip(),
                        "unit": str(item.get("unit", "")).strip(),
                    }
                )
                continue

            included = getattr(item, "included", True)
            if included is False:
                continue
            name = str(getattr(item, "name", "")).strip()
            if not name:
                continue
            details.append(
                {
                    "name": name,
                    "quantity": str(getattr(item, "quantity", "") or "").strip(),
                    "unit": str(getattr(item, "unit", "") or "").strip(),
                }
            )

        return details

    def resolved_cooking_technique(self) -> str:
        return (self.cooking_technique or self.technique or "瀹跺父蹇墜").strip()

    def resolved_equipment(self) -> List[str]:
        return self.equipment or self.tools or ["鐐掗攨", "鐮ф澘", "鍒€"]

    def resolved_flavor_profile(self) -> str:
        if self.flavor_profile and self.flavor_profile.strip():
            return self.flavor_profile.strip()
        if self.tastes:
            return " / ".join([item for item in self.tastes if item])
        return "瀹跺父"


class RecipeImageGenerateRequest(BaseModel):
    recipe: Dict[str, Any]
    cooking_technique: Optional[str] = None
    technique: Optional[str] = None
    flavor_profile: Optional[str] = None
    tastes: List[str] = Field(default_factory=list)

    def resolved_cooking_technique(self) -> str:
        return (self.cooking_technique or self.technique or "").strip()

    def resolved_flavor_profile(self) -> str:
        if self.flavor_profile and self.flavor_profile.strip():
            return self.flavor_profile.strip()
        if self.tastes:
            return " / ".join([item for item in self.tastes if item])
        return ""


class ImageRecognizeRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class UserPreferencesRequest(BaseModel):
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    preferred_cuisines: List[str] = Field(default_factory=list)
    disliked_ingredients: List[str] = Field(default_factory=list)
    preferred_spice_level: int = Field(default=3, ge=1, le=5)
    calorie_target: Optional[int] = None
    meal_preferences: List[str] = Field(default_factory=list)
    equipment_available: List[str] = Field(default_factory=list)


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
    ingredients: List[IngredientInput] = Field(default_factory=list)
    steps: List[dict] = Field(default_factory=list)
    is_published: bool = False
    source: str = "manual"


class GenerationLogRequest(BaseModel):
    user_id: Optional[str] = None
    recognized_ingredients: List[str] = Field(default_factory=list)
    generated_recipe: Dict[str, Any] = Field(default_factory=dict)
    ai_model_used: str = ""
    quality_rating: Optional[int] = None


class ArchiveCreateRequest(BaseModel):
    user_id: str
    title: str
    recipe_id: Optional[str] = None
    generation_log_id: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_shared: bool = False


def _sanitize_storage_name(value: str) -> str:
    ascii_value = value.strip().lower().encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return cleaned or "recipe"


def _build_generation_response(
    recipe_result,
    *,
    image_asset: Optional[Dict[str, Any]] = None,
    recognition: Optional[Dict[str, Any]] = None,
    normality: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    recipe_payload = recipe_result.to_dict()
    response: Dict[str, Any] = {
        "success": True,
        "recipe": recipe_payload,
        "title": recipe_payload.get("title_zh") or recipe_payload.get("title"),
        "summary": recipe_payload.get("description"),
        "steps": recipe_payload.get("steps", []),
    }

    if recognition is not None:
        response["recognition"] = recognition

    if normality:
        response["normality"] = normality
        response["normality_score"] = normality.get("normality_score")
        response["normality_label"] = normality.get("label")
        response["normality_mood"] = normality.get("mood")
        response["normality_text"] = normality.get("text")
        response["normality_level"] = normality.get("level")
        response["normality_verdict"] = normality.get("verdict")

    if image_asset:
        response["imageUrl"] = image_asset.get("url")
        response["boardPreview"] = image_asset.get("url")
        response["storagePath"] = image_asset.get("path")

    return response


def _recipe_result_from_payload(payload: Dict[str, Any]) -> RecipeGenerationResult:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Recipe payload is required")

    title = str(payload.get("title") or payload.get("title_zh") or "").strip()
    title_zh = str(payload.get("title_zh") or payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    tips = str(payload.get("tips") or "").strip()
    image_prompt = str(payload.get("image_prompt") or "").strip()

    ingredients_raw = payload.get("ingredients") if isinstance(payload.get("ingredients"), list) else []
    ingredients: List[Dict[str, Any]] = []
    for item in ingredients_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        ingredients.append(
            {
                "name": name,
                "quantity": str(item.get("quantity") or "").strip(),
                "unit": str(item.get("unit") or "").strip(),
                "notes": str(item.get("notes") or "").strip(),
            }
        )

    steps_raw = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    steps: List[Dict[str, Any]] = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        steps.append(
            {
                "title": str(item.get("title") or "").strip(),
                "instruction": str(item.get("instruction") or "").strip(),
                "duration_minutes": item.get("duration_minutes"),
                "tips": str(item.get("tips") or "").strip(),
            }
        )

    nutrition = payload.get("nutrition") if isinstance(payload.get("nutrition"), dict) else {}

    return RecipeGenerationResult(
        title=title or title_zh or "recipe",
        title_zh=title_zh or title or "recipe",
        description=description,
        ingredients=ingredients,
        steps=steps,
        tips=tips,
        nutrition=nutrition,
        image_prompt=image_prompt,
    )


def _generate_and_store_recipe_image(
    ai,
    recipe_result,
    technique: str,
    flavor_profile: str,
    *,
    suppress_errors: bool = True,
) -> Optional[Dict[str, Any]]:
    if not settings.use_supabase_storage:
        return None

    max_attempts = max(1, int(settings.image_generation_retry_attempts or 1))
    last_error: Optional[AIServiceError] = None

    for attempt in range(1, max_attempts + 1):
        try:
            image_bytes, mime_type, _prompt, remote_url = ai.generate_recipe_image(
                recipe_result,
                cooking_technique=technique,
                flavor_profile=flavor_profile,
            )
            break
        except AIServiceError as error:
            last_error = error
            logger.warning(
                "Recipe image generation attempt %s/%s failed: %s",
                attempt,
                max_attempts,
                error,
            )
            if attempt >= max_attempts:
                if not suppress_errors:
                    raise
                logger.warning("Recipe image generation skipped after retries: %s", error)
                return None
    else:
        if not suppress_errors and last_error is not None:
            raise last_error
        return None

    if remote_url:
        return {
            "path": None,
            "public_url": remote_url,
            "signed_url": None,
            "url": remote_url,
        }

    title = recipe_result.title_zh or recipe_result.title or "recipe"
    filename = f"{_sanitize_storage_name(title)}-{uuid.uuid4().hex[:8]}.png"
    return upload_generated_image(
        image_bytes,
        content_type=mime_type or "image/png",
        prefix="generated",
        filename=filename,
    )


def _decode_image_base64(image_base64: str) -> bytes:
    try:
        payload = image_base64.strip()
        if payload.startswith("data:") and "," in payload:
            payload = payload.split(",", 1)[1]
        return base64.b64decode(payload)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid image_base64 payload") from error


def _frontend_safe_ai_error(
    error: AIServiceError,
    *,
    default_message: str = "Generation did not finish. Please try again.",
) -> HTTPException:
    logger.error("AI flow failed: %s", error)
    message = str(error).strip()
    lowered = message.lower()

    if "not configured" in lowered or "閰嶇疆" in message:
        return HTTPException(
            status_code=503,
            detail="AI configuration is incomplete. Please check server environment variables.",
        )

    return HTTPException(status_code=502, detail=default_message)


def _score_normality(
    ingredients: List[str],
    *,
    cooking_method: Optional[str] = None,
    seasonings: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    try:
        service = get_scorer()
        return service.score(
            ingredients=ingredients,
            cooking_method=(cooking_method or "炒").strip() or "炒",
            seasonings=seasonings,
        )
    except Exception as error:
        logger.warning("Traditional normality scoring skipped: %s", error)
        return None


def _build_fallback_recipe_from_request(request: RecipeGenerateRequest) -> RecipeGenerationResult:
    ingredient_names = request.ingredient_names()
    ingredient_details = request.ingredient_details()
    technique = request.resolved_cooking_technique() or "蹇倰"
    flavor_profile = request.resolved_flavor_profile() or "瀹跺父"
    equipment = request.resolved_equipment()

    detail_map: Dict[str, Dict[str, str]] = {}
    for item in ingredient_details:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        detail_map[name] = item

    strict_ingredients: List[Dict[str, Any]] = []
    for name in ingredient_names:
        detail = detail_map.get(name, {})
        quantity = str(detail.get("quantity", "")).strip() or "閫傞噺"
        unit = str(detail.get("unit", "")).strip()
        strict_ingredients.append(
            {
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "notes": "fallback_recipe",
            }
        )

    if len(ingredient_names) >= 2:
        title_zh = f"{technique}{ingredient_names[0]}{ingredient_names[1]}"
    elif ingredient_names:
        title_zh = f"{technique}{ingredient_names[0]}"
    else:
        title_zh = f"{technique}缁勫悎"

    steps = [
        {
            "title": "鍑嗗椋熸潗",
            "instruction": "将已确认食材洗净、切配，并按主料与辅料分开摆放，方便后续控火。",
            "duration_minutes": 5,
            "tips": "先处理耐火食材，再处理易熟食材。",
        },
        {
            "title": "鐑攨瀹氬瀷",
            "instruction": f"使用 {', '.join(equipment[:2]) if equipment else '常用锅具'} 预热后下主料，按{technique}完成主体上色与定型。",
            "duration_minutes": 8,
            "tips": "保持中高火，避免频繁翻动导致出水。",
        },
        {
            "title": "璋冨懗鏀跺熬",
            "instruction": f"加入辅料快速翻拌，按“{flavor_profile}”方向补齐咸淡与香气，收汁后出锅装盘。",
            "duration_minutes": 6,
            "tips": "出锅前尝味，最后 30 秒再做微调。",
        },
    ]

    nutrition = {
        "calories_per_serving": 220 + len(ingredient_names) * 70,
        "protein_g": 12 + len(ingredient_names) * 3,
        "fat_g": 8 + len(ingredient_names),
        "carbs_g": 15 + len(ingredient_names) * 4,
    }

    return RecipeGenerationResult(
        title=title_zh,
        title_zh=title_zh,
        description=f"已根据本次确认食材生成应急菜谱，技法偏{technique}，风味偏{flavor_profile}。",
        ingredients=strict_ingredients,
        steps=steps,
        tips="当前为应急生成版本，可直接用于演示与流程验证。",
        nutrition=nutrition,
        image_prompt="",
    )


def _generate_recipe_with_local_fallback(
    ai_client,
    *,
    request: RecipeGenerateRequest,
    ingredient_names: List[str],
    ingredient_details: List[Dict[str, str]],
    technique: str,
    flavor_profile: str,
    equipment: List[str],
) -> tuple[RecipeGenerationResult, bool]:
    try:
        result = ai_client.generate_recipe(
            ingredients=ingredient_names,
            ingredient_details=ingredient_details,
            cooking_technique=technique,
            flavor_profile=flavor_profile,
            spice_level=request.spice_level,
            max_time=request.max_time,
            equipment=equipment,
        )
        return result, False
    except AIServiceError as error:
        logger.warning("AI recipe generation failed, using local fallback recipe: %s", error)
        return _build_fallback_recipe_from_request(request), True


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "instant-food-backend",
    }


@router.get("/ai/status")
async def ai_status() -> Dict[str, Any]:
    ai = get_ai_client()
    normality_service = get_scorer()
    return {
        "available": ai.is_available,
        "provider": settings.ai_provider,
        "text_available": ai.text_available,
        "vision_available": ai.vision_available,
        "image_available": ai.image_available,
        "traditional_normality_available": normality_service.available,
        "model": settings.ai_model if settings.has_gemini() else None,
        "vision_model": settings.vision_model if settings.has_gemini() else None,
        "image_model": settings.image_model if settings.has_gemini() else None,
        "backup_provider": settings.backup_provider_name if settings.has_backup_api() else None,
        "backup_text_model": settings.backup_text_model if settings.has_backup_text_model() else None,
        "backup_image_model": settings.backup_image_model if settings.has_backup_image_model() else None,
    }


@router.post("/generate/from-image")
async def generate_from_image(request: ImageRecognizeRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.vision_available:
        raise HTTPException(status_code=503, detail="Image recognition service not available")

    try:
        if request.image_base64:
            recognition_result = ai.recognize_image_with_fallback(_decode_image_base64(request.image_base64))
        elif request.image_url:
            recognition_result = ai.recognize_image_from_url_with_fallback(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")

        ingredient_names = [
            item.get("name", "")
            for item in recognition_result.ingredients
            if isinstance(item, dict) and item.get("name")
        ]
        ingredient_details = [
            {
                "name": str(item.get("name", "")).strip(),
                "quantity": str(item.get("estimated_quantity", "")).strip(),
                "unit": "",
            }
            for item in recognition_result.ingredients
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
        recipe_result = ai.generate_recipe(
            ingredients=ingredient_names,
            ingredient_details=ingredient_details,
            cooking_technique=recognition_result.cooking_method,
            flavor_profile="瀹跺父",
        )
        normality_result = _score_normality(
            ingredient_names,
            cooking_method=recognition_result.cooking_method,
        )
        image_asset = _generate_and_store_recipe_image(
            ai,
            recipe_result,
            recognition_result.cooking_method,
            "瀹跺父",
        )

        try:
            get_supabase_admin().table("generation_logs").insert(
                {
                    "recognized_ingredients": ingredient_names,
                    "generated_recipe": recipe_result.to_dict(),
                    "ai_model_used": settings.ai_model,
                    "quality_rating": None,
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        except Exception as log_error:
            logger.warning("Failed to log generation: %s", log_error)

        return _build_generation_response(
            recipe_result,
            image_asset=image_asset,
            recognition=recognition_result.to_dict(),
            normality=normality_result,
        )
    except AIServiceError as error:
        raise _frontend_safe_ai_error(
            error,
            default_message="Recognition and generation did not finish. Please try again.",
        ) from error


@router.post("/generate/recipe")
async def generate_recipe(request: RecipeGenerateRequest, include_image: bool = True) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.text_available:
        raise HTTPException(status_code=503, detail="Recipe generation service not available")

    ingredient_names = request.ingredient_names()
    if not ingredient_names:
        raise HTTPException(status_code=400, detail="At least one ingredient is required")

    technique = request.resolved_cooking_technique()
    flavor_profile = request.resolved_flavor_profile()
    ingredient_details = request.ingredient_details()
    equipment = request.resolved_equipment()

    try:
        recipe_result, used_local_fallback = _generate_recipe_with_local_fallback(
            ai,
            request=request,
            ingredient_names=ingredient_names,
            ingredient_details=ingredient_details,
            technique=technique,
            flavor_profile=flavor_profile,
            equipment=equipment,
        )
        normality_result = _score_normality(
            ingredient_names,
            cooking_method=technique,
        )
        image_asset = None
        if include_image and ai.image_available:
            image_asset = _generate_and_store_recipe_image(ai, recipe_result, technique, flavor_profile)
        return _build_generation_response(
            recipe_result,
            image_asset=image_asset,
            normality=normality_result,
        )
    except AIServiceError as error:
        raise _frontend_safe_ai_error(
            error,
            default_message="Generation did not finish. Please try again.",
        ) from error


@router.post("/generate/image")
async def generate_recipe_image(request: RecipeImageGenerateRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.image_available:
        raise HTTPException(status_code=503, detail="Image generation service not available")

    recipe_result = _recipe_result_from_payload(request.recipe)
    technique = request.resolved_cooking_technique()
    flavor_profile = request.resolved_flavor_profile()

    try:
        image_asset = _generate_and_store_recipe_image(
            ai,
            recipe_result,
            technique,
            flavor_profile,
            suppress_errors=False,
        )
    except AIServiceError as error:
        raise _frontend_safe_ai_error(
            error,
            default_message="Image generation did not finish. Please try again.",
        ) from error

    if not image_asset or not image_asset.get("url"):
        raise HTTPException(
            status_code=502,
            detail="Image generation did not finish. Please try again.",
        )

    return {
        "success": True,
        "imageUrl": image_asset.get("url"),
        "boardPreview": image_asset.get("url"),
        "storagePath": image_asset.get("path"),
    }


@router.post("/recognize/image")
async def recognize_image(request: ImageRecognizeRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.vision_available:
        raise HTTPException(status_code=503, detail="Image recognition service not available")

    try:
        if request.image_base64:
            result = ai.recognize_image_with_fallback(_decode_image_base64(request.image_base64))
        elif request.image_url:
            result = ai.recognize_image_from_url_with_fallback(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")
        return {"success": True, "result": result.to_dict()}
    except AIServiceError as error:
        raise _frontend_safe_ai_error(
            error,
            default_message="Recognition did not finish. Please try again.",
        ) from error


@router.post("/recipes")
async def create_recipe(request: RecipeCreateRequest) -> Dict[str, Any]:
    try:
        supabase = get_supabase_admin()
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
            "is_ai_generated": request.source == "ai_generated",
        }
        recipe_response = supabase.table("recipes").insert(recipe_data).execute()
        recipe = recipe_response.data[0] if recipe_response.data else None
        if not recipe:
            raise HTTPException(status_code=500, detail="Failed to create recipe")

        for index, ingredient in enumerate(request.ingredients):
            supabase.table("recipe_ingredients").insert(
                {
                    "recipe_id": recipe["id"],
                    "ingredient_name": ingredient.name,
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                    "notes": ingredient.notes,
                    "sort_order": index,
                }
            ).execute()

        for index, step in enumerate(request.steps):
            supabase.table("recipe_steps").insert(
                {
                    "recipe_id": recipe["id"],
                    "step_number": index + 1,
                    "instruction": step.get("instruction", ""),
                    "instruction_zh": step.get("instruction_zh"),
                    "duration_minutes": step.get("duration_minutes"),
                    "tips": step.get("tips"),
                }
            ).execute()

        return {"success": True, "recipe": recipe}
    except HTTPException:
        raise
    except Exception as error:
        logger.error("Create recipe failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/recipes")
async def list_recipes(
    limit: int = 20,
    offset: int = 0,
    cuisine_type: Optional[str] = None,
    meal_type: Optional[str] = None,
    published_only: bool = True,
) -> Dict[str, Any]:
    try:
        query = get_supabase().table("recipes").select("*")
        if published_only:
            query = query.eq("is_published", True)
        if cuisine_type:
            query = query.eq("cuisine_type", cuisine_type)
        if meal_type:
            query = query.eq("meal_type", meal_type)
        response = query.range(offset, offset + limit - 1).order("created_at", ascending=False).execute()
        return {
            "success": True,
            "recipes": response.data,
            "count": len(response.data),
        }
    except Exception as error:
        logger.error("List recipes failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str) -> Dict[str, Any]:
    try:
        supabase = get_supabase()
        recipe_response = supabase.table("recipes").select("*").eq("id", recipe_id).execute()
        if not recipe_response.data:
            raise HTTPException(status_code=404, detail="Recipe not found")

        recipe = recipe_response.data[0]
        ingredients_response = (
            supabase.table("recipe_ingredients")
            .select("*")
            .eq("recipe_id", recipe_id)
            .order("sort_order")
            .execute()
        )
        steps_response = (
            supabase.table("recipe_steps")
            .select("*")
            .eq("recipe_id", recipe_id)
            .order("step_number")
            .execute()
        )
        recipe["ingredients"] = ingredients_response.data
        recipe["steps"] = steps_response.data
        return {"success": True, "recipe": recipe}
    except HTTPException:
        raise
    except Exception as error:
        logger.error("Get recipe failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str) -> Dict[str, Any]:
    try:
        get_supabase_admin().table("recipes").delete().eq("id", recipe_id).execute()
        return {"success": True, "message": "Recipe deleted"}
    except Exception as error:
        logger.error("Delete recipe failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/ingredients")
async def list_ingredients(limit: int = 50, offset: int = 0, category: Optional[str] = None) -> Dict[str, Any]:
    try:
        query = get_supabase().table("ingredients").select("*")
        if category:
            query = query.eq("category", category)
        response = query.range(offset, offset + limit - 1).execute()
        return {
            "success": True,
            "ingredients": response.data,
            "count": len(response.data),
        }
    except Exception as error:
        logger.error("List ingredients failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/ingredients/search")
async def search_ingredients(q: str, limit: int = 20) -> Dict[str, Any]:
    try:
        response = (
            get_supabase()
            .table("ingredients")
            .select("*")
            .or_(f"name.ilike.%{q}%,name_zh.ilike.%{q}%")
            .limit(limit)
            .execute()
        )
        return {
            "success": True,
            "ingredients": response.data,
            "count": len(response.data),
        }
    except Exception as error:
        logger.error("Search ingredients failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/flavor-profiles")
async def list_flavor_profiles() -> Dict[str, Any]:
    try:
        response = get_supabase().table("flavor_profiles").select("*").execute()
        return {"success": True, "profiles": response.data}
    except Exception as error:
        logger.error("List flavor profiles failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/cooking-techniques")
async def list_cooking_techniques() -> Dict[str, Any]:
    try:
        response = get_supabase().table("cooking_techniques").select("*").execute()
        return {"success": True, "techniques": response.data}
    except Exception as error:
        logger.error("List cooking techniques failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/user/preferences")
async def save_user_preferences(user_id: str, request: UserPreferencesRequest) -> Dict[str, Any]:
    try:
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
            "updated_at": datetime.utcnow().isoformat(),
        }
        get_supabase_admin().table("user_preferences").upsert(
            preferences_data, on_conflict="user_id"
        ).execute()
        return {"success": True, "message": "Preferences saved"}
    except Exception as error:
        logger.error("Save preferences failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/user/preferences/{user_id}")
async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    try:
        response = get_supabase().table("user_preferences").select("*").eq("user_id", user_id).execute()
        if not response.data:
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
                    "equipment_available": ["鐐掗攨", "鐮ф澘", "鍒€"],
                },
            }
        return {"success": True, "preferences": response.data[0]}
    except Exception as error:
        logger.error("Get preferences failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/generation/log")
async def log_generation(request: GenerationLogRequest) -> Dict[str, Any]:
    try:
        response = get_supabase_admin().table("generation_logs").insert(
            {
                "user_id": request.user_id,
                "recognized_ingredients": request.recognized_ingredients,
                "generated_recipe": request.generated_recipe,
                "ai_model_used": request.ai_model_used or settings.ai_model,
                "quality_rating": request.quality_rating,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
        return {"success": True, "log_id": response.data[0]["id"] if response.data else None}
    except Exception as error:
        logger.error("Log generation failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/training/export")
async def export_training_data(limit: int = 1000) -> Dict[str, Any]:
    try:
        response = (
            get_supabase_admin()
            .table("generation_logs")
            .select("*")
            .gte("quality_rating", 4)
            .limit(limit)
            .execute()
        )
        training_data = [
            {
                "input": f"椋熸潗: {', '.join(log.get('recognized_ingredients', []))}",
                "output": log.get("generated_recipe", {}),
                "quality_rating": log.get("quality_rating"),
            }
            for log in response.data
        ]
        return {
            "success": True,
            "count": len(training_data),
            "data": training_data,
        }
    except Exception as error:
        logger.error("Export training data failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/archives")
async def list_archives(user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    try:
        query = get_supabase_admin().table("archives").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return {
            "success": True,
            "archives": response.data,
            "count": len(response.data),
        }
    except Exception as error:
        logger.error("List archives failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/archives")
async def create_archive(request: ArchiveCreateRequest) -> Dict[str, Any]:
    try:
        response = get_supabase_admin().table("archives").insert(
            {
                "user_id": request.user_id,
                "title": request.title,
                "recipe_id": request.recipe_id,
                "generation_log_id": request.generation_log_id,
                "cover_image_url": request.cover_image_url,
                "is_shared": request.is_shared,
                "shared_at": datetime.utcnow().isoformat() if request.is_shared else None,
            }
        ).execute()
        return {
            "success": True,
            "archive": response.data[0] if response.data else None,
        }
    except Exception as error:
        logger.error("Create archive failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error

