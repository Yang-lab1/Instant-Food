"""
香疯了 - 识图服务
==================
拍冰箱照片 → 调多模态 LLM → 返回食材列表

调用方式：
    recognizer = ImageRecognizer()
    recognizer.init()
    result = await recognizer.recognize(image_base64)
    # result = {"ingredients": ["鸡蛋", "番茄", "牛奶", ...]}
"""

import os
import json
import httpx


class ImageRecognizer:
    def __init__(self):
        self.api_key = None
        self.base_url = None
        self.model = None

    def init(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("VISION_MODEL", "deepseek-ai/deepseek-vl2")

        if not self.api_key:
            raise ValueError("❌ LLM_API_KEY 环境变量未设置")
        print(f"✅ 识图服务初始化完成 (模型: {self.model})")

    async def recognize(self, image_base64: str) -> dict:
        """
        输入冰箱照片的 base64 编码，返回识别到的食材列表。

        参数：
            image_base64: 图片的 base64 字符串（不含 data:image/... 前缀）

        返回：
            {
                "ingredients": ["鸡蛋", "番茄", "牛奶", ...],
                "raw_response": "模型原始回复"
            }
        """
        prompt = """请仔细观察这张冰箱/食材照片，识别出所有可见的食材和食品。

要求：
1. 只列出你能确认看到的食材，不要猜测
2. 用常见的中文食材名（如"鸡蛋"而非"蛋类"）
3. 调料也要列出（如酱油、盐等）
4. 严格按 JSON 格式返回，不要包含任何其他文字

返回格式：
{"ingredients": ["食材1", "食材2", "食材3"]}"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1,  # 低温度，让识别更稳定
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

        # 解析 JSON（模型可能会在 JSON 外面加 markdown 代码块）
        ingredients = self._parse_ingredients(raw_text)

        return {
            "ingredients": ingredients,
            "raw_response": raw_text,
        }

    def _parse_ingredients(self, text: str) -> list[str]:
        """从模型回复中提取食材列表，容错处理"""
        # 去掉可能的 markdown 代码块标记
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # 去掉 ```json 和 ```
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "ingredients" in parsed:
                return parsed["ingredients"]
            elif isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # JSON 解析失败，尝试用简单规则提取
        # 找到 [ ] 之间的内容
        import re
        match = re.search(r'\[([^\]]+)\]', text)
        if match:
            items = match.group(1)
            # 提取引号中的内容
            return re.findall(r'["\']([^"\']+)["\']', items)

        # 最后兜底：按行分割
        return [line.strip().strip("-•·") for line in text.split("\n") if line.strip()]
