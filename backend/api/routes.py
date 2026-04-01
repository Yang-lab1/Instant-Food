"""
拍立食 - API 路由
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

from api.ai_client import AIServiceError, get_ai_client
from config import settings
from database.supabase_client import (
    get_supabase,
    get_supabase_admin,
    upload_generated_image,
)

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
    flavor_profile: str = "家常"
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

    def resolved_cooking_technique(self) -> str:
        return (self.cooking_technique or self.technique or "家常快手").strip()

    def resolved_equipment(self) -> List[str]:
        return self.equipment or self.tools or ["炒锅", "砧板", "刀"]

    def resolved_flavor_profile(self) -> str:
        if self.flavor_profile and self.flavor_profile.strip():
            return self.flavor_profile.strip()
        if self.tastes:
            return " / ".join([item for item in self.tastes if item])
        return "家常"


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

    if image_asset:
        response["imageUrl"] = image_asset.get("url")
        response["boardPreview"] = image_asset.get("url")
        response["storagePath"] = image_asset.get("path")

    return response


def _generate_and_store_recipe_image(ai, recipe_result, technique: str, flavor_profile: str) -> Optional[Dict[str, Any]]:
    if not settings.use_supabase_storage:
        return None

    image_bytes, mime_type, _prompt = ai.generate_recipe_image(
        recipe_result,
        cooking_technique=technique,
        flavor_profile=flavor_profile,
    )
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
        return base64.b64decode(image_base64)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid image_base64 payload") from error


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
    return {
        "available": ai.is_available,
        "provider": settings.ai_provider,
        "model": settings.ai_model if ai.is_available else None,
        "vision_model": settings.vision_model if ai.is_available else None,
        "image_model": settings.image_model if ai.is_available else None,
    }


@router.post("/generate/from-image")
async def generate_from_image(request: ImageRecognizeRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        if request.image_base64:
            recognition_result = ai.recognize_image(_decode_image_base64(request.image_base64))
        elif request.image_url:
            recognition_result = ai.recognize_image_from_url(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")

        ingredient_names = [
            item.get("name", "")
            for item in recognition_result.ingredients
            if isinstance(item, dict) and item.get("name")
        ]
        recipe_result = ai.generate_recipe(
            ingredients=ingredient_names,
            cooking_technique=recognition_result.cooking_method,
            flavor_profile="家常",
        )
        image_asset = _generate_and_store_recipe_image(
            ai,
            recipe_result,
            recognition_result.cooking_method,
            "家常",
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
        )
    except AIServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/generate/recipe")
async def generate_recipe(request: RecipeGenerateRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")

    ingredient_names = request.ingredient_names()
    if not ingredient_names:
        raise HTTPException(status_code=400, detail="At least one ingredient is required")

    try:
        technique = request.resolved_cooking_technique()
        flavor_profile = request.resolved_flavor_profile()
        recipe_result = ai.generate_recipe(
            ingredients=ingredient_names,
            cooking_technique=technique,
            flavor_profile=flavor_profile,
            spice_level=request.spice_level,
            max_time=request.max_time,
            equipment=request.resolved_equipment(),
        )
        image_asset = _generate_and_store_recipe_image(ai, recipe_result, technique, flavor_profile)
        return _build_generation_response(recipe_result, image_asset=image_asset)
    except AIServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/recognize/image")
async def recognize_image(request: ImageRecognizeRequest) -> Dict[str, Any]:
    ai = get_ai_client()
    if not ai.is_available:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        if request.image_base64:
            result = ai.recognize_image(_decode_image_base64(request.image_base64))
        elif request.image_url:
            result = ai.recognize_image_from_url(request.image_url)
        else:
            raise HTTPException(status_code=400, detail="Either image_url or image_base64 required")
        return {"success": True, "result": result.to_dict()}
    except AIServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


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
                    "equipment_available": ["炒锅", "砧板", "刀"],
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
                "input": f"食材: {', '.join(log.get('recognized_ingredients', []))}",
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
        query = get_supabase().table("archives").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.range(offset, offset + limit - 1).order("created_at", ascending=False).execute()
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
