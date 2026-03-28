"""
拍立食 - Google Gemini AI 服务客户端
"""
import base64
import json
import logging
import time
from typing import Optional, Dict, Any, List

import google.generativeai as genai
import httpx

from config import settings

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Gemini 服务错误"""
    pass


class ImageRecognitionResult:
    """图片识别结果"""
    def __init__(
        self,
        ingredients: List[Dict[str, Any]],
        cooking_method: str,
        nutrition_notes: str,
        allergen_warning: List[str]
    ):
        self.ingredients = ingredients
        self.cooking_method = cooking_method
        self.nutrition_notes = nutrition_notes
        self.allergen_warning = allergen_warning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ingredients": self.ingredients,
            "cooking_method": self.cooking_method,
            "nutrition_notes": self.nutrition_notes,
            "allergen_warning": self.allergen_warning
        }


class RecipeGenerationResult:
    """食谱生成结果"""
    def __init__(
        self,
        title: str,
        title_zh: str,
        description: str,
        ingredients: List[Dict[str, Any]],
        steps: List[Dict[str, Any]],
        tips: str,
        nutrition: Dict[str, Any]
    ):
        self.title = title
        self.title_zh = title_zh
        self.description = description
        self.ingredients = ingredients
        self.steps = steps
        self.tips = tips
        self.nutrition = nutrition
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "title_zh": self.title_zh,
            "description": self.description,
            "ingredients": self.ingredients,
            "steps": self.steps,
            "tips": self.tips,
            "nutrition": self.nutrition
        }


class ImageGenerationResult:
    """图片生成结果"""
    def __init__(
        self,
        image_base64: str,
        mime_type: str = "image/png",
        text: str = ""
    ):
        self.image_base64 = image_base64
        self.mime_type = mime_type
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_base64": self.image_base64,
            "mime_type": self.mime_type,
            "text": self.text
        }


class GeminiClient:
    """Gemini AI 客户端"""
    
    # 图片识别 Prompt
    IMAGE_RECOGNITION_PROMPT = """请分析这张食物图片，识别出主要的食材成分。

请以JSON格式输出，包含以下字段：
- ingredients: 食材列表，每项包含 name(食材名), estimated_quantity(估计用量), confidence(置信度 0-1)
- cooking_method: 烹饪方式（如炒、煮、蒸、烤、炸、生食等）
- nutrition_notes: 营养特点简述
- allergen_warning: 可能存在的过敏原列表（如牛奶、鸡蛋、小麦、甲壳类等）

只输出JSON，不要有其他文字。"""
    
    # 食谱生成 Prompt 模板
    RECIPE_GENERATION_PROMPT_TEMPLATE = """你是一位专业的中餐厨师，擅长根据用户提供的食材创作美味的食谱。

食材: {ingredients_list}
用户偏好:
- 烹饪技法: {cooking_technique}
- 风味档案: {flavor_profile}
- 辣度: {spice_level}/5
- 时间限制: {max_time}分钟
- 可用厨具: {equipment}

要求:
1. 食谱要有创意但实用，适合中国家庭厨房
2. 步骤清晰易操作
3. 包含营养信息和过敏原提醒
4. 考虑用户的口味偏好和可用设备

请以JSON格式输出:
{{
  "title": "食谱英文名",
  "title_zh": "食谱中文名",
  "description": "简介",
  "ingredients": [
    {{"name": "食材名", "quantity": "用量", "unit": "单位", "notes": "处理备注"}}
  ],
  "steps": [
    {{"instruction": "步骤描述", "duration_minutes": 分钟数, "tips": "小贴士"}}
  ],
  "tips": "整体小贴士",
  "nutrition": {{
    "calories_per_serving": 总卡路里,
    "protein_g": 蛋白质克数,
    "fat_g": 脂肪克数,
    "carbs_g": 碳水克数
  }},
  "allergen_warning": ["过敏原提醒"],
  "health_tips": ["健康建议"]
}}

只输出JSON，不要有其他文字。"""
    
    def __init__(self):
        self._client: Optional[genai.GenerativeModel] = None
        self._vision_client: Optional[genai.GenerativeModel] = None
        
        if settings.has_gemini():
            genai.configure(api_key=settings.gemini_api_key)
            self._client = genai.GenerativeModel(settings.ai_model)
            self._vision_client = genai.GenerativeModel(settings.vision_model)
            logger.info(f"Gemini client initialized with model: {settings.ai_model}")
    
    @property
    def is_available(self) -> bool:
        """检查 Gemini 服务是否可用"""
        return self._client is not None
    
    def recognize_image(self, image_data: bytes, image_type: str = "image/jpeg") -> ImageRecognitionResult:
        """
        识别图片中的食材
        
        Args:
            image_data: 图片二进制数据
            image_type: MIME 类型
        
        Returns:
            ImageRecognitionResult: 识别结果
        """
        if not settings.has_gemini():
            raise GeminiServiceError("Gemini API key not configured")
        
        start_time = time.time()
        
        # 将图片转换为 base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 确定图片类型
        if image_type == "image/png":
            mime_type = "image/png"
        else:
            mime_type = "image/jpeg"
        
        try:
            # 构建提示
            prompt = self.IMAGE_RECOGNITION_PROMPT
            
            # 生成内容
            response = self._vision_client.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": base64_image
                }
            ])
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Image recognition completed in {elapsed_ms}ms")
            
            return self._parse_image_result(response.text)
            
        except Exception as e:
            logger.error(f"Image recognition failed: {e}")
            raise GeminiServiceError(f"Image recognition failed: {str(e)}")
    
    def recognize_image_from_url(self, image_url: str) -> ImageRecognitionResult:
        """从 URL 识别图片（需要下载图片）"""
        import httpx
        
        if not settings.has_gemini():
            raise GeminiServiceError("Gemini API key not configured")
        
        start_time = time.time()
        
        try:
            # 下载图片
            response = httpx.get(image_url, timeout=30.0)
            response.raise_for_status()
            image_data = response.content
            
            # 确定 MIME 类型
            content_type = response.headers.get("content-type", "image/jpeg")
            
            return self.recognize_image(image_data, content_type)
            
        except Exception as e:
            logger.error(f"Image recognition from URL failed: {e}")
            raise GeminiServiceError(f"Image recognition failed: {str(e)}")
    
    def generate_recipe(
        self,
        ingredients: List[str],
        cooking_technique: str = "炒",
        flavor_profile: str = "川菜",
        spice_level: int = 3,
        max_time: int = 30,
        equipment: List[str] = None,
        prompt_override: Optional[str] = None
    ) -> RecipeGenerationResult:
        """
        根据食材生成食谱
        
        Args:
            ingredients: 食材列表
            cooking_technique: 烹饪技法
            flavor_profile: 风味档案
            spice_level: 辣度 1-5
            max_time: 最大时间（分钟）
            equipment: 可用厨具
        
        Returns:
            RecipeGenerationResult: 生成的食谱
        """
        if not settings.has_gemini():
            raise GeminiServiceError("Gemini API key not configured")
        
        if equipment is None:
            equipment = ["炒锅", "砧板", "菜刀"]
        
        start_time = time.time()
        
        prompt = prompt_override or self.RECIPE_GENERATION_PROMPT_TEMPLATE.format(
            ingredients_list=", ".join(ingredients),
            cooking_technique=cooking_technique,
            flavor_profile=flavor_profile,
            spice_level=spice_level,
            max_time=max_time,
            equipment=", ".join(equipment)
        )
        
        try:
            response = self._client.generate_content(prompt)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Recipe generation completed in {elapsed_ms}ms")
            
            return self._parse_recipe_result(response.text)
            
        except Exception as e:
            logger.error(f"Recipe generation failed: {e}")
            raise GeminiServiceError(f"Recipe generation failed: {str(e)}")
    
    def _parse_image_result(self, content: str) -> ImageRecognitionResult:
        """解析图片识别结果"""
        # 提取 JSON
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        json_str = json_str.strip()
        data = json.loads(json_str)
        
        return ImageRecognitionResult(
            ingredients=data.get("ingredients", []),
            cooking_method=data.get("cooking_method", "未知"),
            nutrition_notes=data.get("nutrition_notes", ""),
            allergen_warning=data.get("allergen_warning", [])
        )
    
    def _parse_recipe_result(self, content: str) -> RecipeGenerationResult:
        """解析食谱生成结果"""
        # 提取 JSON
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        json_str = json_str.strip()
        data = json.loads(json_str)
        
        return RecipeGenerationResult(
            title=data.get("title", ""),
            title_zh=data.get("title_zh", data.get("title", "")),
            description=data.get("description", ""),
            ingredients=data.get("ingredients", []),
            steps=data.get("steps", []),
            tips=data.get("tips", ""),
            nutrition=data.get("nutrition", {})
        )

    def generate_dish_image(self, prompt: str) -> ImageGenerationResult:
        """调用 Gemini 图像生成模型（Nano Banana / gemini-2.5-flash-image）。"""
        if not settings.has_gemini():
            raise GeminiServiceError("Gemini API key not configured")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.image_model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }

        try:
            response = httpx.post(url, json=payload, timeout=90.0)
            response.raise_for_status()
            data = response.json()
            return self._parse_image_generation_result(data)
        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}")
            raise GeminiServiceError(f"Image generation failed: {str(e)}")

    def _parse_image_generation_result(self, data: Dict[str, Any]) -> ImageGenerationResult:
        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                inline_data = part.get("inlineData") or part.get("inline_data")
                if inline_data:
                    return ImageGenerationResult(
                        image_base64=inline_data.get("data", ""),
                        mime_type=inline_data.get("mimeType", "image/png"),
                        text=next(
                            (
                                item.get("text", "")
                                for item in content.get("parts", [])
                                if item.get("text")
                            ),
                            "",
                        ),
                    )

        raise GeminiServiceError("Image generation returned no image data")


# 全局 Gemini 客户端实例
gemini_client = GeminiClient()


def get_gemini_client() -> GeminiClient:
    """获取 Gemini 客户端"""
    return gemini_client
