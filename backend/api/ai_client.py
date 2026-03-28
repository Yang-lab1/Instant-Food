"""
拍立食 - AI 服务客户端
仅从 ai_training_data 数据库提取食谱信息
"""
from collections import Counter
import logging
import time
from typing import Optional, Dict, Any, List

from database.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI 服务错误"""
    pass


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
    """统一 AI 服务客户端 - 仅从 ai_training_data 数据库提取食谱"""
    
    def __init__(self):
        self._training_rows_cache: List[Dict[str, Any]] = []

    def _load_training_rows(self) -> List[Dict[str, Any]]:
        """带重试地读取 ai_training_data，并缓存最近一次成功结果。"""
        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                supabase = get_supabase_admin()
                response = (
                    supabase.table("ai_training_data")
                    .select("input_description,expected_output,quality_score")
                    .order("quality_score", desc=True)
                    .limit(120)
                    .execute()
                )
                rows = response.data or []
                if rows:
                    self._training_rows_cache = rows
                return rows
            except Exception as exc:
                last_error = exc
                time.sleep(0.25 * (attempt + 1))

        if self._training_rows_cache:
            logger.warning(
                "Failed to load AI training examples from Supabase, using cached rows instead: %s",
                last_error,
            )
            return self._training_rows_cache

        logger.warning(f"Failed to load AI training examples: {last_error}")
        return []

    def _fetch_training_examples(self, ingredients: List[str], limit: int = 1) -> List[Dict[str, Any]]:
        """从 ai_training_data 中挑选与当前输入最相关的样本。"""
        rows = self._load_training_rows()
        if not rows:
            return []

        lowered_ingredients = [item.lower() for item in ingredients if item]
        scored = []
        for row in rows:
            input_description = (row.get("input_description") or "").lower()
            expected_output = (row.get("expected_output") or "").lower()
            score = sum(
                1 for ingredient in lowered_ingredients
                if ingredient in input_description or ingredient in expected_output
            )
            score += float(row.get("quality_score") or 0)
            scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        matched_rows = [row for score, row in scored if score > 0][:limit]
        if matched_rows:
            return matched_rows

        return rows[:1]

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
        根据食材从数据库生成食谱
        
        Args:
            ingredients: 食材列表
            cooking_technique: 烹饪技法（参考用，主要从数据库提取）
            flavor_profile: 风味档案（参考用，主要从数据库提取）
            spice_level: 辣度 1-5（参考用，主要从数据库提取）
            max_time: 最大时间（参考用，主要从数据库提取）
            equipment: 可用厨具（参考用，主要从数据库提取）
        
        Returns:
            RecipeGenerationResult: 生成的食谱
        """
        return self._build_recipe_from_training_data(
            ingredients=ingredients,
            cooking_technique=cooking_technique,
            flavor_profile=flavor_profile,
            spice_level=spice_level,
            max_time=max_time,
        )

    def _build_recipe_from_training_data(
        self,
        ingredients: List[str],
        cooking_technique: str,
        flavor_profile: str,
        spice_level: int,
        max_time: int,
    ) -> RecipeGenerationResult:
        """仅根据 ai_training_data.input_description 组织文字结果。"""
        training_examples = self._fetch_training_examples(ingredients)
        counts = Counter([item.strip() for item in ingredients if item.strip()])
        ingredient_items = []

        quantity_map = {
            "鸡蛋": "个",
            "番茄": "个",
            "西红柿": "个",
            "葱": "根",
        }

        for name, count in counts.items():
            unit = quantity_map.get(name, "份")
            ingredient_items.append(
                {
                    "name": name,
                    "quantity": str(count),
                    "unit": unit,
                    "notes": infer_training_note(name),
                }
            )

        top_example = training_examples[0] if training_examples else None
        input_description = top_example.get("input_description") if top_example else ""

        title_zh = build_fallback_title(
            list(counts.keys()),
            cooking_technique,
            top_example=top_example,
        )
        description = extract_description_from_training(input_description) or (
            f"基于训练库检索结果整理出的{flavor_profile}风味做法，主要食材为 {'、'.join(counts.keys())}。"
        )
        steps = build_fallback_steps(
            list(counts.keys()),
            cooking_technique,
            spice_level,
            input_description=input_description,
        )
        nutrition = estimate_fallback_nutrition(counts)
        tips = build_training_tips(input_description, ingredients, max_time)

        return RecipeGenerationResult(
            title=title_zh,
            title_zh=title_zh,
            description=description,
            ingredients=ingredient_items,
            steps=steps,
            tips=tips,
            nutrition=nutrition,
        )


# 全局 AI 客户端实例
ai_client = AIClient()


def get_ai_client() -> AIClient:
    """获取 AI 客户端"""
    return ai_client


def build_fallback_title(
    ingredients: List[str],
    cooking_technique: str,
    top_example: Optional[Dict[str, Any]] = None,
) -> str:
    if top_example and top_example.get("expected_output"):
        return top_example["expected_output"]
    lead = "".join(ingredients[:2]) if ingredients else "家常料理"
    return f"{lead}{cooking_technique}"


def infer_training_note(name: str) -> str:
    """从训练数据推断食材处理建议"""
    if name in {"鸡蛋", "鸭蛋", "鹌鹑蛋"}:
        return "建议打散或单独处理后再合入主菜。"
    if name in {"番茄", "西红柿"}:
        return "适合先切块，烹饪时可利用其自然出汁。"
    if name in {"葱", "姜", "蒜"}:
        return "通常用于提香，建议切小备用。"
    return "根据训练库相近做法，建议先洗净并按菜式切配。"


def extract_description_from_training(input_description: str) -> str:
    text = input_description or ""
    marker = "简介："
    if marker in text:
        tail = text.split(marker, 1)[1]
        for stop in ["步骤：", "关键词："]:
            if stop in tail:
                tail = tail.split(stop, 1)[0]
        return tail.strip(" ，。")
    return ""


def extract_steps_text_from_description(input_description: str) -> str:
    text = input_description or ""
    marker = "步骤："
    if marker in text:
        tail = text.split(marker, 1)[1]
        if "关键词：" in tail:
            tail = tail.split("关键词：", 1)[0]
        return tail.strip(" ，。")
    return ""


def build_fallback_steps(
    ingredients: List[str],
    cooking_technique: str,
    spice_level: int,
    input_description: str = "",
) -> List[Dict[str, Any]]:
    """从训练数据获取烹饪步骤"""
    generated_from_training = build_steps_from_training_description(input_description)
    if generated_from_training:
        return generated_from_training
    return [
        {
            "instruction": build_generic_flow_text(ingredients, cooking_technique, spice_level),
            "duration_minutes": 0,
            "tips": "当前流程说明基于输入食材自动整理，建议结合现场状态微调火候。"
        }
    ]


def build_steps_from_training_description(input_description: str) -> List[Dict[str, Any]]:
    """从训练数据描述中提取步骤"""
    text = (input_description or "").strip()
    if not text:
        return []

    flow_text = extract_steps_text_from_description(text)
    if not flow_text:
        return []

    return [
        {
            "instruction": flow_text,
            "duration_minutes": 0,
            "tips": "以下流程说明直接根据 ai_training_data 的 input_description 整理。"
        }
    ]


def estimate_fallback_nutrition(counts: Counter) -> Dict[str, Any]:
    """估算营养信息"""
    eggs = counts.get("鸡蛋", 0)
    tomatoes = counts.get("番茄", 0) + counts.get("西红柿", 0)
    return {
        "calories_per_serving": 120 * eggs + 25 * tomatoes,
        "protein_g": 6 * eggs,
        "fat_g": 5 * eggs,
        "carbs_g": 5 * tomatoes,
    }


def build_training_tips(input_description: str, ingredients: List[str], max_time: int) -> str:
    extracted = extract_steps_text_from_description(input_description)
    if extracted:
        return f"已根据训练库中的相关做法整理流程，建议在约 {max_time} 分钟内按顺序完成。"
    return f"当前结果主要依据输入食材 {'、'.join(ingredients)} 和训练库相关文本整理而成。"


def build_generic_flow_text(ingredients: List[str], cooking_technique: str, spice_level: int) -> str:
    joined = "、".join(ingredients) if ingredients else "当前食材"
    spice_text = "清淡" if spice_level <= 2 else "偏重口" if spice_level >= 4 else "中等"
    return (
        f"先将{joined}按菜式需要完成清洗和切配，再根据{cooking_technique}方式依次下锅处理。"
        f"烹饪过程中保持{spice_text}风味方向，按食材成熟度补充基础调味，确认口感后出锅即可。"
    )
