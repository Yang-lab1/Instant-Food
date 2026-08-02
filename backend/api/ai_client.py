"""
拍立食 - AI 服务客户端

策略：
1. 主模型优先走 Gemini。
2. 若 Gemini 失败且已配置备用模型，则自动降级到备用模型。
3. 若主备都失败，返回统一“请再试一次”的用户文案，避免把底层原始报错直接暴露给前端。
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI 服务错误。"""


class ImageRecognitionResult:
    """图片识别结果。"""

    def __init__(
        self,
        ingredients: List[Dict[str, Any]],
        cooking_method: str,
        nutrition_notes: str,
        allergen_warning: List[str],
    ) -> None:
        self.ingredients = ingredients
        self.cooking_method = cooking_method
        self.nutrition_notes = nutrition_notes
        self.allergen_warning = allergen_warning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ingredients": self.ingredients,
            "cooking_method": self.cooking_method,
            "nutrition_notes": self.nutrition_notes,
            "allergen_warning": self.allergen_warning,
        }


class RecipeGenerationResult:
    """食谱生成结果。"""

    def __init__(
        self,
        title: str,
        title_zh: str,
        description: str,
        ingredients: List[Dict[str, Any]],
        steps: List[Dict[str, Any]],
        tips: str,
        nutrition: Dict[str, Any],
        image_prompt: str = "",
    ) -> None:
        self.title = title
        self.title_zh = title_zh
        self.description = description
        self.ingredients = ingredients
        self.steps = steps
        self.tips = tips
        self.nutrition = nutrition
        self.image_prompt = image_prompt

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "title": self.title,
            "title_zh": self.title_zh,
            "description": self.description,
            "ingredients": self.ingredients,
            "steps": self.steps,
            "tips": self.tips,
            "nutrition": self.nutrition,
        }
        if self.image_prompt:
            payload["image_prompt"] = self.image_prompt
        return payload


class AIClient:
    """Gemini 优先，支持备用模型降级的 AI 客户端。"""

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
    USER_RETRY_MESSAGE = "暂未完成生成，请再试一次。"
    USER_RETRY_IMAGE_MESSAGE = "图片暂未完成，请再试一次。"

    IMAGE_RECOGNITION_PROMPT = """
请分析这张食物图片，并严格输出 JSON。

输出格式：
{
  "ingredients": [
    {"name": "食材名称", "estimated_quantity": "估计用量", "confidence": 0.0}
  ],
  "cooking_method": "烹饪方式",
  "nutrition_notes": "营养特点",
  "allergen_warning": ["可能过敏原"]
}

要求：
1. 只输出 JSON，不要额外说明。
2. ingredients 至少返回 1 个项目。
3. confidence 使用 0 到 1 的数值。
""".strip()

    RECIPE_GENERATION_PROMPT_TEMPLATE = """
你是一位专业主厨，请根据给定食材生成一份适合 H5 展示的食谱，并严格输出 JSON。

输入信息：
- 食材：{ingredients_list}
- 烹饪技法：{cooking_technique}
- 风味方向：{flavor_profile}
- 辣度：{spice_level}/5
- 最大时长：{max_time} 分钟
- 可用厨具：{equipment}

输出格式：
{{
  "title": "英文或创意标题",
  "title_zh": "中文菜名",
  "description": "一句简介",
  "ingredients": [
    {{"name": "食材名称", "quantity": "数量", "unit": "单位", "notes": "备注"}}
  ],
  "steps": [
    {{
      "title": "步骤标题",
      "instruction": "步骤描述",
      "duration_minutes": 5,
      "tips": "小贴士"
    }}
  ],
  "tips": "整道菜的提示",
  "nutrition": {{
    "calories_per_serving": 520,
    "protein_g": 28,
    "fat_g": 18,
    "carbs_g": 35
  }},
  "image_prompt": "用于生成成品图的简洁描述"
}}

要求：
1. 只输出 JSON。
2. title_zh、description、ingredients、steps 必须存在。
3. 风格适合移动端结果页展示，避免过长。
""".strip()

    def __init__(self) -> None:
        timeout = httpx.Timeout(connect=15.0, read=90.0, write=90.0, pool=15.0)
        self._http = httpx.Client(timeout=timeout)

        if settings.has_gemini():
            logger.info("Gemini primary model ready: %s", settings.ai_model)
        else:
            logger.warning("Gemini API key missing; primary model unavailable.")

        if settings.has_backup_text_model():
            logger.info(
                "Backup text model ready: provider=%s model=%s",
                settings.backup_provider_name,
                settings.backup_text_model,
            )
        elif settings.backup_text_model:
            logger.warning("Backup text model configured but BACKUP_API_KEY/BACKUP_API_BASE_URL is missing.")

        if settings.has_backup_image_model():
            logger.info(
                "Backup image model ready: provider=%s model=%s",
                settings.backup_provider_name,
                settings.backup_image_model,
            )

    @property
    def is_available(self) -> bool:
        return self.text_available

    @property
    def text_available(self) -> bool:
        return settings.has_gemini() or settings.has_backup_text_model()

    @property
    def vision_available(self) -> bool:
        return settings.has_gemini()

    @property
    def image_available(self) -> bool:
        return settings.has_gemini() or settings.has_backup_image_model()

    def recognize_image(self, image_data: bytes, image_type: str = "image/jpeg") -> ImageRecognitionResult:
        if not settings.has_gemini():
            raise AIServiceError("图片识别服务暂不可用，请检查 Gemini 配置。")

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": self.IMAGE_RECOGNITION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": image_type,
                                "data": base64.b64encode(image_data).decode("utf-8"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": settings.max_tokens,
                "responseMimeType": "application/json",
            },
        }
        response_json = self._gemini_request(settings.vision_model, payload)
        text = self._extract_text(response_json)
        return self._parse_image_result(text)

    def recognize_image_from_url(self, image_url: str) -> ImageRecognitionResult:
        if not settings.has_gemini():
            raise AIServiceError("图片识别服务暂不可用，请检查 Gemini 配置。")

        try:
            response = self._http.get(image_url)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise AIServiceError(f"Failed to download source image: {error}") from error

        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip() or "image/jpeg"
        return self.recognize_image(response.content, content_type)

    def generate_recipe(
        self,
        ingredients: List[str],
        ingredient_details: Optional[List[Dict[str, Any]]] = None,
        cooking_technique: str = "煎炒",
        flavor_profile: str = "家常",
        spice_level: int = 3,
        max_time: int = 30,
        equipment: Optional[List[str]] = None,
    ) -> RecipeGenerationResult:
        if not self.text_available:
            raise AIServiceError("食谱生成服务暂不可用，请检查 AI 配置。")

        equipment = equipment or ["炒锅", "砧板", "刀"]
        prompt = self.RECIPE_GENERATION_PROMPT_TEMPLATE.format(
            ingredients_list=", ".join(ingredients),
            cooking_technique=cooking_technique,
            flavor_profile=flavor_profile,
            spice_level=spice_level,
            max_time=max_time,
            equipment=", ".join(equipment),
        )
        prompt += (
            "\n\nHard constraints:\n"
            "- Use ONLY the provided ingredients.\n"
            "- Do NOT introduce any extra ingredient names.\n"
            "- The JSON `ingredients` array must match the provided ingredient names exactly (same set).\n"
            "- The cooking steps must not require any ingredient outside that list.\n"
        )

        primary_error: Optional[Exception] = None
        if settings.has_gemini():
            try:
                result = self._generate_recipe_with_gemini(prompt)
                return self._enforce_requested_ingredients(
                    result,
                    ingredients,
                    ingredient_details=ingredient_details,
                    cooking_technique=cooking_technique,
                    flavor_profile=flavor_profile,
                    equipment=equipment,
                )
            except AIServiceError as error:
                primary_error = error
                logger.warning("Gemini recipe generation failed, fallback will be attempted: %s", error)

        if settings.has_backup_text_model():
            try:
                result = self._generate_recipe_with_backup(prompt)
                return self._enforce_requested_ingredients(
                    result,
                    ingredients,
                    ingredient_details=ingredient_details,
                    cooking_technique=cooking_technique,
                    flavor_profile=flavor_profile,
                    equipment=equipment,
                )
            except AIServiceError as backup_error:
                logger.error("Backup recipe generation failed: %s", backup_error)
                if primary_error:
                    logger.error("Primary failure before backup: %s", primary_error)
                raise AIServiceError(self.USER_RETRY_MESSAGE) from backup_error

        if primary_error:
            raise AIServiceError(self.USER_RETRY_MESSAGE) from primary_error

        raise AIServiceError("食谱生成服务暂不可用，请检查模型配置。")

    def generate_recipe_image(
        self,
        recipe: RecipeGenerationResult,
        cooking_technique: str = "",
        flavor_profile: str = "",
    ) -> Tuple[bytes, str, str]:
        if not self.image_available:
            raise AIServiceError("图片生成服务暂不可用，请检查模型配置。")

        prompt = recipe.image_prompt or self._build_image_prompt(recipe, cooking_technique, flavor_profile)

        primary_error: Optional[Exception] = None
        if settings.has_gemini():
            try:
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.8,
                        "responseModalities": ["TEXT", "IMAGE"],
                    },
                }
                response_json = self._gemini_request(settings.image_model, payload)
                image_bytes, mime_type = self._extract_inline_image(response_json)
                return image_bytes, mime_type, prompt
            except AIServiceError as error:
                primary_error = error
                logger.warning("Gemini image generation failed, fallback will be attempted: %s", error)

        if settings.has_backup_image_model():
            try:
                image_bytes, mime_type = self._generate_image_with_backup(prompt)
                return image_bytes, mime_type, prompt
            except AIServiceError as backup_error:
                logger.error("Backup image generation failed: %s", backup_error)
                if primary_error:
                    logger.error("Primary image failure before backup: %s", primary_error)
                raise AIServiceError(self.USER_RETRY_IMAGE_MESSAGE) from backup_error

        if primary_error:
            raise AIServiceError(self.USER_RETRY_IMAGE_MESSAGE) from primary_error

        raise AIServiceError("图片生成服务暂不可用，请检查模型配置。")

    def _generate_recipe_with_gemini(self, prompt: str) -> RecipeGenerationResult:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_tokens,
                "responseMimeType": "application/json",
            },
        }
        response_json = self._gemini_request(settings.ai_model, payload)
        text = self._extract_text(response_json)

        try:
            return self._parse_recipe_result(text)
        except AIServiceError as error:
            if "Invalid recipe JSON" not in str(error):
                raise

        logger.warning("Gemini returned invalid JSON, retrying once with stricter instruction.")
        retry_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                prompt
                                + "\n\nIMPORTANT:\n"
                                  "- Return STRICT parseable JSON only.\n"
                                  "- No markdown fences.\n"
                                  "- No comments.\n"
                                  "- No trailing commas.\n"
                                  "- No extra explanation text.\n"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": settings.max_tokens,
                "responseMimeType": "application/json",
            },
        }
        retry_response_json = self._gemini_request(settings.ai_model, retry_payload)
        retry_text = self._extract_text(retry_response_json)
        return self._parse_recipe_result(retry_text)

    def _generate_recipe_with_backup(self, prompt: str) -> RecipeGenerationResult:
        text = self._backup_chat_completion(prompt, require_json_mode=True)
        try:
            return self._parse_recipe_result(text)
        except AIServiceError as error:
            if "Invalid recipe JSON" not in str(error):
                raise

        logger.warning("Backup model returned invalid JSON, retrying once without JSON mode requirement.")
        retry_prompt = (
            prompt
            + "\n\nIMPORTANT:\n"
              "- Return STRICT parseable JSON only.\n"
              "- No markdown fences.\n"
              "- No comments.\n"
              "- No trailing commas.\n"
              "- No extra explanation text.\n"
        )
        retry_text = self._backup_chat_completion(retry_prompt, require_json_mode=False)
        return self._parse_recipe_result(retry_text)

    def _generate_image_with_backup(self, prompt: str) -> Tuple[bytes, str]:
        if not settings.has_backup_image_model():
            raise AIServiceError("Backup image model not configured")

        payload: Dict[str, Any] = {
            "model": settings.backup_image_model,
            "prompt": prompt,
            "size": "1024x1024",
            "response_format": "b64_json",
        }

        try:
            response_json = self._backup_request("/images/generations", payload)
        except AIServiceError as error:
            if self._supports_response_format_retry(str(error)):
                logger.warning("Backup image API rejected response_format, retrying without it.")
                payload.pop("response_format", None)
                response_json = self._backup_request("/images/generations", payload)
            else:
                raise

        data_items = response_json.get("data") or []
        if not data_items:
            raise AIServiceError("Backup image API returned no data")

        first_item = data_items[0] if isinstance(data_items[0], dict) else {}
        b64_json = first_item.get("b64_json")
        if b64_json:
            try:
                return base64.b64decode(b64_json), "image/png"
            except Exception as decode_error:
                raise AIServiceError("Backup image API returned invalid b64 data") from decode_error

        image_url = first_item.get("url")
        if image_url:
            return self._download_image_as_bytes(image_url)

        raise AIServiceError("Backup image API returned neither b64_json nor url")

    def _backup_chat_completion(self, prompt: str, require_json_mode: bool) -> str:
        if not settings.has_backup_text_model():
            raise AIServiceError("Backup text model not configured")

        payload: Dict[str, Any] = {
            "model": settings.backup_text_model,
            "messages": [
                {"role": "system", "content": "你是食谱生成助手，输出必须可被程序解析。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }
        if require_json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response_json = self._backup_request("/chat/completions", payload)
        except AIServiceError as error:
            if require_json_mode and self._supports_response_format_retry(str(error)):
                logger.warning("Backup chat API rejected response_format, retrying without response_format.")
                payload.pop("response_format", None)
                response_json = self._backup_request("/chat/completions", payload)
            else:
                raise

        return self._extract_backup_chat_text(response_json)

    def _backup_request(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        base_url = (settings.backup_api_base_url or "").rstrip("/")
        api_key = settings.backup_api_key or ""
        if not base_url or not api_key:
            raise AIServiceError("Backup API is not fully configured")

        url = f"{base_url}{path}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._http.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            body = error.response.text
            logger.error("Backup model HTTP error (%s): %s", error.response.status_code, body[:2000])
            raise AIServiceError(f"Backup model request failed: {body}") from error
        except httpx.HTTPError as error:
            logger.error("Backup model network error: %s", error)
            raise AIServiceError(f"Backup model network error: {error}") from error
        except ValueError as error:
            logger.error("Backup model response parse error: %s", error)
            raise AIServiceError("Backup model returned invalid JSON response") from error

    def _gemini_request(self, model: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.GEMINI_API_BASE}/{model}:generateContent"
        headers = {
            "x-goog-api-key": settings.gemini_api_key or "",
            "Content-Type": "application/json",
        }

        try:
            response = self._http.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            body = error.response.text
            logger.error("Gemini request failed: %s", body[:2000])
            raise AIServiceError(f"Gemini request failed: {body}") from error
        except httpx.HTTPError as error:
            logger.error("Gemini network error: %s", error)
            raise AIServiceError(f"Gemini network error: {error}") from error
        except ValueError as error:
            logger.error("Gemini response parse error: %s", error)
            raise AIServiceError("Gemini returned invalid JSON response") from error

    @staticmethod
    def _extract_text(response_json: Dict[str, Any]) -> str:
        candidates = response_json.get("candidates") or []
        if not candidates:
            raise AIServiceError("Gemini returned no candidates")

        parts = candidates[0].get("content", {}).get("parts") or []
        text_chunks = [part.get("text", "") for part in parts if part.get("text")]
        text = "\n".join(text_chunks).strip()
        if not text:
            raise AIServiceError("Gemini returned no text content")
        return text

    @staticmethod
    def _extract_inline_image(response_json: Dict[str, Any]) -> Tuple[bytes, str]:
        candidates = response_json.get("candidates") or []
        if not candidates:
            raise AIServiceError("Gemini returned no candidates")

        parts = candidates[0].get("content", {}).get("parts") or []
        for part in parts:
            blob = part.get("inlineData") or part.get("inline_data")
            if not blob:
                continue

            data = blob.get("data")
            mime_type = blob.get("mimeType") or blob.get("mime_type") or "image/png"
            if data:
                try:
                    return base64.b64decode(data), mime_type
                except Exception as decode_error:
                    raise AIServiceError("Gemini returned invalid image data") from decode_error

        raise AIServiceError("Gemini returned no image data")

    def _download_image_as_bytes(self, image_url: str) -> Tuple[bytes, str]:
        try:
            response = self._http.get(image_url)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise AIServiceError(f"Failed to download backup image: {error}") from error

        content_type = response.headers.get("content-type", "image/png").split(";")[0].strip() or "image/png"
        return response.content, content_type

    @staticmethod
    def _extract_backup_chat_text(response_json: Dict[str, Any]) -> str:
        choices = response_json.get("choices") or []
        if not choices:
            raise AIServiceError("Backup chat API returned no choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            text = content.strip()
            if text:
                return text

        if isinstance(content, list):
            text_chunks: List[str] = []
            for part in content:
                if isinstance(part, str):
                    if part.strip():
                        text_chunks.append(part.strip())
                    continue
                if isinstance(part, dict):
                    text_value = part.get("text") or part.get("content")
                    if isinstance(text_value, str) and text_value.strip():
                        text_chunks.append(text_value.strip())
            text = "\n".join(text_chunks).strip()
            if text:
                return text

        raise AIServiceError("Backup chat API returned empty text content")

    @staticmethod
    def _supports_response_format_retry(error_text: str) -> bool:
        text = str(error_text or "").lower()
        indicators = [
            "response_format",
            "json_object",
            "unsupported",
            "not supported",
            "invalid request",
        ]
        return any(indicator in text for indicator in indicators)

    @staticmethod
    def _strip_json_fence(content: str) -> str:
        text = content.strip()
        if text.startswith("```json"):
            return text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("```"):
            return text.split("```", 1)[1].rsplit("```", 1)[0].strip()
        return text

    @staticmethod
    def _extract_json_object(text: str) -> str:
        source = text.strip()
        start = source.find("{")
        end = source.rfind("}")
        if start != -1 and end != -1 and end > start:
            return source[start : end + 1]
        return source

    @staticmethod
    def _sanitize_json_text(content: str) -> str:
        text = AIClient._strip_json_fence(content)
        text = AIClient._extract_json_object(text)
        text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
        text = text.replace("\ufeff", "")
        text = re.sub(r",\s*([}\]])", r"\1", text)
        text = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or ord(ch) >= 32)
        return text.strip()

    def _parse_image_result(self, content: str) -> ImageRecognitionResult:
        try:
            data = json.loads(self._sanitize_json_text(content))
        except json.JSONDecodeError as error:
            raise AIServiceError(f"Invalid image recognition JSON: {content}") from error

        return ImageRecognitionResult(
            ingredients=data.get("ingredients", []),
            cooking_method=data.get("cooking_method", "未知"),
            nutrition_notes=data.get("nutrition_notes", ""),
            allergen_warning=data.get("allergen_warning", []),
        )

    def _parse_recipe_result(self, content: str) -> RecipeGenerationResult:
        try:
            data = json.loads(self._sanitize_json_text(content))
        except json.JSONDecodeError as error:
            raise AIServiceError(f"Invalid recipe JSON: {content}") from error

        return RecipeGenerationResult(
            title=data.get("title", ""),
            title_zh=data.get("title_zh", data.get("title", "")),
            description=data.get("description", ""),
            ingredients=data.get("ingredients", []),
            steps=data.get("steps", []),
            tips=data.get("tips", ""),
            nutrition=data.get("nutrition", {}),
            image_prompt=data.get("image_prompt", ""),
        )

    @staticmethod
    def _normalize_ingredient_token(value: str) -> str:
        return "".join(str(value or "").strip().lower().split())

    def _enforce_requested_ingredients(
        self,
        recipe: RecipeGenerationResult,
        requested_ingredients: List[str],
        ingredient_details: Optional[List[Dict[str, Any]]] = None,
        cooking_technique: str = "",
        flavor_profile: str = "",
        equipment: Optional[List[str]] = None,
    ) -> RecipeGenerationResult:
        requested: List[str] = []
        seen = set()
        for name in requested_ingredients:
            cleaned = str(name or "").strip()
            if not cleaned:
                continue
            token = self._normalize_ingredient_token(cleaned)
            if token in seen:
                continue
            seen.add(token)
            requested.append(cleaned)

        if not requested:
            return recipe

        if not isinstance(recipe.ingredients, list):
            recipe.ingredients = []

        normalized_ingredients: List[Dict[str, Any]] = []
        for item in recipe.ingredients:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                normalized_ingredients.append(
                    {
                        "name": name,
                        "quantity": str(item.get("quantity", "")).strip(),
                        "unit": str(item.get("unit", "")).strip(),
                        "notes": str(item.get("notes", "")).strip(),
                    }
                )
            elif isinstance(item, str) and item.strip():
                normalized_ingredients.append(
                    {
                        "name": item.strip(),
                        "quantity": "moderate",
                        "unit": "",
                        "notes": "",
                    }
                )

        token_to_item: Dict[str, Dict[str, Any]] = {}
        for item in normalized_ingredients:
            token = self._normalize_ingredient_token(item.get("name", ""))
            if token and token not in token_to_item:
                token_to_item[token] = item

        detail_map: Dict[str, Dict[str, str]] = {}
        for detail in ingredient_details or []:
            if not isinstance(detail, dict):
                continue
            name = str(detail.get("name", "")).strip()
            if not name:
                continue
            token = self._normalize_ingredient_token(name)
            if not token or token in detail_map:
                continue
            detail_map[token] = {
                "name": name,
                "quantity": str(detail.get("quantity", "")).strip(),
                "unit": str(detail.get("unit", "")).strip(),
            }

        strict_ingredients: List[Dict[str, Any]] = []
        for requested_name in requested:
            token = self._normalize_ingredient_token(requested_name)
            matched = token_to_item.get(token, {})
            detail = detail_map.get(token, {})
            quantity = (
                str(detail.get("quantity", "")).strip()
                or str(matched.get("quantity", "")).strip()
                or "moderate"
            )
            unit = str(detail.get("unit", "")).strip() or str(matched.get("unit", "")).strip()
            notes = str(matched.get("notes", "")).strip() or "user_selected_ingredient"
            strict_ingredients.append(
                {
                    "name": requested_name,
                    "quantity": quantity,
                    "unit": unit,
                    "notes": notes,
                }
            )

        recipe.ingredients = strict_ingredients

        ingredient_spec_parts: List[str] = []
        for item in strict_ingredients:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            quantity = str(item.get("quantity", "")).strip()
            unit = str(item.get("unit", "")).strip()
            if quantity:
                ingredient_spec_parts.append(f"{name}: {quantity}{unit}".strip())
            else:
                ingredient_spec_parts.append(name)
        ingredient_spec_text = "; ".join(ingredient_spec_parts)
        allowed_ingredients_text = ", ".join(requested)
        technique_text = (cooking_technique or "").strip() or "user-selected technique"
        flavor_text = (flavor_profile or "").strip() or "user-selected flavor profile"
        equipment_text = ", ".join([str(item).strip() for item in (equipment or []) if str(item).strip()]) or "user-selected cookware"
        recipe.image_prompt = (
            "Michelin three-star fine dining hero dish, ultra-photorealistic food photography, "
            "elegant minimalist plating, premium restaurant table styling, moody cinematic low-key lighting, "
            "matte dark tabletop, refined ceramic plate, subtle linen texture, premium cutlery details, "
            "soft bokeh background, editorial composition for luxury dining magazine. "
            "Composition requirement: single hero plate centered in the frame (horizontal center + vertical center), "
            "dish occupies about 60-75% of visual focus, avoid off-center subject. "
            f"Allowed edible ingredients ONLY: {allowed_ingredients_text}. "
            f"Exact ingredient quantities and units to respect: {ingredient_spec_text}. "
            "Quantity ratio is a hard constraint: visual weight and portion balance must not deviate from the provided ratio. "
            f"Cooking technique focus: {technique_text}. Flavor direction: {flavor_text}. Cookware context: {equipment_text}. "
            "Do NOT add any extra edible ingredient, garnish, sauce, herb, fruit, vegetable, side dish, or dessert not listed above. "
            "Background props must be non-edible only (plate, cutlery, table linen, tableware), no extra food props. "
            "No text overlay, no logo, no watermark, no cartoon style."
        )

        return recipe

    @staticmethod
    def _build_image_prompt(
        recipe: RecipeGenerationResult,
        cooking_technique: str,
        flavor_profile: str,
    ) -> str:
        title = recipe.title_zh or recipe.title or "Chef special"
        ingredient_specs = []
        for item in recipe.ingredients:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            quantity = str(item.get("quantity", "")).strip()
            unit = str(item.get("unit", "")).strip()
            if quantity:
                ingredient_specs.append(f"{name}: {quantity}{unit}".strip())
            else:
                ingredient_specs.append(name)

        flavor_hint = flavor_profile or "user-selected flavor profile"
        technique_hint = cooking_technique or "user-selected technique"

        return (
            "Michelin three-star fine dining hero dish, ultra-photorealistic food photography, "
            f"dish title: {title}. "
            f"Allowed ingredients with quantity/unit: {'; '.join(ingredient_specs) or 'user confirmed ingredients only'}. "
            "Quantity ratio is mandatory and cannot deviate visually. "
            "Dark luxury restaurant table ambience, matte dark tabletop, premium ceramic plate, "
            "subtle linen texture and elegant cutlery, moody cinematic lighting, shallow depth of field. "
            "Composition requirement: single hero plate centered in frame, dish as clear visual center, not off to edges. "
            f"Technique focus: {technique_hint}. Flavor direction: {flavor_hint}. "
            "No extra edible ingredient, garnish, sauce, or side dish; no edible background props. "
            "No cartoon style, no text, no logo, no watermark."
        )


ai_client = AIClient()


def get_ai_client() -> AIClient:
    return ai_client
