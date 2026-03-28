"""
拍立食 - AI 服务客户端
统一 AI 服务入口，优先支持 OpenAI / Gemini
"""
import base64
import json
import logging
import time
from typing import Optional, Dict, Any, List

from openai import OpenAI
import anthropic

from config import settings
from api.gemini_client import get_gemini_client, GeminiServiceError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI 服务错误"""
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


class AIClient:
    """统一 AI 服务客户端"""
    
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
        self._openai_client: Optional[OpenAI] = None
        self._anthropic_client: Optional[anthropic.Anthropic] = None
        self._gemini_client = get_gemini_client()
        
        if settings.has_openai():
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info(f"OpenAI client initialized with model: {settings.ai_model}")
        
        if settings.has_anthropic():
            self._anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
    
    @property
    def is_available(self) -> bool:
        """检查 AI 服务是否可用"""
        return (
            self._openai_client is not None
            or self._anthropic_client is not None
            or self._gemini_client.is_available
        )

    @property
    def provider_name(self) -> str:
        """当前可用的 AI 提供商。"""
        if self._openai_client is not None:
            return "openai"
        if self._gemini_client.is_available:
            return "gemini"
        if self._anthropic_client is not None:
            return "anthropic"
        return "none"

    @property
    def model_name(self) -> Optional[str]:
        """当前启用的模型名称。"""
        if self.provider_name == "none":
            return None
        return settings.ai_model
    
    def recognize_image(self, image_data: bytes, image_type: str = "image/jpeg") -> ImageRecognitionResult:
        """
        识别图片中的食材
        
        Args:
            image_data: 图片二进制数据
            image_type: MIME 类型
        
        Returns:
            ImageRecognitionResult: 识别结果
        """
        if self._openai_client is None and self._gemini_client.is_available:
            try:
                result = self._gemini_client.recognize_image(image_data, image_type)
                return ImageRecognitionResult(
                    ingredients=result.ingredients,
                    cooking_method=result.cooking_method,
                    nutrition_notes=result.nutrition_notes,
                    allergen_warning=result.allergen_warning,
                )
            except GeminiServiceError as e:
                raise AIServiceError(str(e))

        if not settings.has_openai():
            raise AIServiceError("OpenAI API key not configured")
        
        start_time = time.time()
        
        # 将图片转换为 base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = self._openai_client.chat.completions.create(
                model=settings.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.IMAGE_RECOGNITION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Image recognition completed in {elapsed_ms}ms")
            
            content = response.choices[0].message.content
            return self._parse_image_result(content)
            
        except Exception as e:
            logger.error(f"Image recognition failed: {e}")
            raise AIServiceError(f"Image recognition failed: {str(e)}")
    
    def recognize_image_from_url(self, image_url: str) -> ImageRecognitionResult:
        """从 URL 识别图片"""
        if self._openai_client is None and self._gemini_client.is_available:
            try:
                result = self._gemini_client.recognize_image_from_url(image_url)
                return ImageRecognitionResult(
                    ingredients=result.ingredients,
                    cooking_method=result.cooking_method,
                    nutrition_notes=result.nutrition_notes,
                    allergen_warning=result.allergen_warning,
                )
            except GeminiServiceError as e:
                raise AIServiceError(str(e))

        if not settings.has_openai():
            raise AIServiceError("OpenAI API key not configured")
        
        start_time = time.time()
        
        try:
            response = self._openai_client.chat.completions.create(
                model=settings.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.IMAGE_RECOGNITION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Image recognition from URL completed in {elapsed_ms}ms")
            
            content = response.choices[0].message.content
            return self._parse_image_result(content)
            
        except Exception as e:
            logger.error(f"Image recognition from URL failed: {e}")
            raise AIServiceError(f"Image recognition failed: {str(e)}")
    
    def generate_recipe(
        self,
        ingredients: List[str],
        cooking_technique: str = "炒",
        flavor_profile: str = "川菜",
        spice_level: int = 3,
        max_time: int = 30,
        equipment: List[str] = None
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
        if self._openai_client is None and self._gemini_client.is_available:
            try:
                result = self._gemini_client.generate_recipe(
                    ingredients=ingredients,
                    cooking_technique=cooking_technique,
                    flavor_profile=flavor_profile,
                    spice_level=spice_level,
                    max_time=max_time,
                    equipment=equipment,
                )
                return RecipeGenerationResult(
                    title=result.title,
                    title_zh=result.title_zh,
                    description=result.description,
                    ingredients=result.ingredients,
                    steps=result.steps,
                    tips=result.tips,
                    nutrition=result.nutrition,
                )
            except GeminiServiceError as e:
                raise AIServiceError(str(e))

        if not settings.has_openai():
            raise AIServiceError("OpenAI API key not configured")
        
        if equipment is None:
            equipment = ["炒锅", "砧板", "菜刀"]
        
        start_time = time.time()
        
        prompt = self.RECIPE_GENERATION_PROMPT_TEMPLATE.format(
            ingredients_list=", ".join(ingredients),
            cooking_technique=cooking_technique,
            flavor_profile=flavor_profile,
            spice_level=spice_level,
            max_time=max_time,
            equipment=", ".join(equipment)
        )
        
        try:
            response = self._openai_client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": "你是一位专业的中餐厨师。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Recipe generation completed in {elapsed_ms}ms")
            
            content = response.choices[0].message.content
            return self._parse_recipe_result(content)
            
        except Exception as e:
            logger.error(f"Recipe generation failed: {e}")
            raise AIServiceError(f"Recipe generation failed: {str(e)}")
    
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


# 全局 AI 客户端实例
ai_client = AIClient()


def get_ai_client() -> AIClient:
    """获取 AI 客户端"""
    return ai_client
