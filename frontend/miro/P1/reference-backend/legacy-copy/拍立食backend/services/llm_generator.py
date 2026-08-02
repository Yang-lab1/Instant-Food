"""
香疯了 - LLM 创意菜谱生成服务（疯了路线）
==========================================

调用方式：
    generator = LLMGenerator()
    generator.init()
    result = await generator.generate(["鸡蛋", "番茄", "可乐"])
"""

import os
import json
import httpx


class LLMGenerator:
    def __init__(self):
        self.api_key = None
        self.base_url = None
        self.model = None

    def init(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("CHAT_MODEL", "deepseek-ai/DeepSeek-V3")

        if not self.api_key:
            raise ValueError("❌ LLM_API_KEY 环境变量未设置")
        print(f"✅ LLM 生成服务初始化完成 (模型: {self.model})")

    async def generate(self, ingredients: list[str]) -> dict:
        """
        给定食材列表，让 LLM 自由发挥生成创意菜谱。

        参数：
            ingredients: ["鸡蛋", "番茄", "可乐"]

        返回：
            {
                "dish_name": "可乐番茄滑蛋",
                "ingredients_used": ["鸡蛋", "番茄", "可乐"],
                "seasonings_suggested": ["盐", "胡椒粉"],
                "steps": ["1. ...", "2. ...", ...],
                "creativity_note": "灵感来自...",
                "raw_response": "..."
            }
        """
        ingredient_str = "、".join(ingredients)

        prompt = f"""你是一个疯狂但有趣的创意厨师。用户冰箱里有这些食材：{ingredient_str}

请你自由发挥，创造一道有趣的创意菜谱。可以大胆、可以离谱、但要确保理论上能做出来（不要有安全隐患）。

严格按以下 JSON 格式返回，不要包含其他文字：
{{
    "dish_name": "你起的创意菜名",
    "ingredients_used": ["用到的食材"],
    "seasonings_suggested": ["建议额外加的调料"],
    "steps": ["步骤1", "步骤2", "步骤3"],
    "creativity_note": "一句话说说你的创意灵感",
    "estimated_time_min": 预计时间（分钟数字）
}}"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个创意十足的厨师，擅长用普通食材做出意想不到的菜。回复必须是纯 JSON，不要有任何其他文字。",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1500,
            "temperature": 0.9,  # 高温度，让生成更有创意
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        raw_text = data["choices"][0]["message"]["content"]
        recipe = self._parse_recipe(raw_text)
        recipe["raw_response"] = raw_text

        return recipe

    def _parse_recipe(self, text: str) -> dict:
        """从模型回复中提取菜谱 JSON，容错处理"""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            )

        try:
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError:
            pass

        # JSON 解析失败，尝试提取 { } 之间的内容
        import re
        match = re.search(r'\{[\s\S]+\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 完全解析失败，返回原文作为兜底
        return {
            "dish_name": "创意料理",
            "ingredients_used": [],
            "seasonings_suggested": [],
            "steps": [text],
            "creativity_note": "LLM 返回格式异常，显示原始回复",
        }
