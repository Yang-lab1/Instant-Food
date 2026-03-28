# AI 客户端简化文档

## 变更概述

已将 AI 客户端从支持多个远程 API 的复杂系统（OpenAI、Anthropic、Gemini）简化为**仅从 Supabase 的 `ai_training_data` 表提取食谱信息**。

## 移除的功能

✗ OpenAI 集成  
✗ Anthropic Claude 集成  
✗ Gemini 客户端集成  
✗ 图片识别功能 (`recognize_image`, `recognize_image_from_url`)  
✗ AI 模型配置 (`provider_name`, `model_name`, `is_available` 等属性)  
✗ 所有 JSON 解析逻辑 (`_parse_image_result`, `_parse_recipe_result`)

## 保留的核心功能

✓ **从数据库查询**：`_load_training_rows()` - 从 `ai_training_data` 表读取数据  
✓ **相关性匹配**：`_fetch_training_examples()` - 根据食材匹配相关的训练数据  
✓ **食谱生成**：`generate_recipe()` - 从数据库构建食谱结果

## 操作流程

### 1. 食材输入
```python
recipe = ai_client.generate_recipe(
    ingredients=["鸡蛋", "番茄", "葱"],
    cooking_technique="炒",
    flavor_profile="川菜",
    spice_level=3,
    max_time=30
)
```

### 2. 操作流程说明
从 `ai_training_data.input_description` 中提取：
- **简介段**：通过 `extract_description_from_training()` 提取
- **步骤段**：通过 `extract_steps_text_from_description()` 提取
- 格式：标记为 `"简介："` 和 `"步骤："` 的文本

### 3. 补充提示
从数据库生成相关答案：
```python
tips = build_training_tips(input_description, ingredients, max_time)
```
返回值：
- 如果找到步骤说明：`"已根据训练库中的相关做法整理流程，建议在约 {max_time} 分钟内按顺序完成。"`
- 否则：`"当前结果主要依据输入食材 ... 和训练库相关文本整理而成。"`

## 数据库查询

### 选择的字段
```sql
SELECT input_description, expected_output, quality_score
FROM ai_training_data
ORDER BY quality_score DESC
LIMIT 120
```

### 数据格式示例

`input_description` 字段应遵循以下格式：
```
简介：这是一道传统的番茄鸡蛋汤。
步骤：先打散鸡蛋，番茄切块；起锅下油爆香葱段，下番茄翻炒出汁；加入清汤烧开，下蛋花搅散；调味即可。
关键词：快手料理、家常汤品
```

## 依赖关系

**内部函数调用路线**：
```
generate_recipe()
  └─ _build_recipe_from_training_data()
      ├─ _fetch_training_examples()
      │   └─ _load_training_rows()
      ├─ build_fallback_title()
      ├─ extract_description_from_training()
      ├─ build_fallback_steps()
      │   └─ build_steps_from_training_description()
      │       └─ extract_steps_text_from_description()
      ├─ estimate_fallback_nutrition()
      ├─ build_training_tips()
      │   └─ extract_steps_text_from_description()
      └─ build_generic_flow_text()
```

## 返回值结构

### RecipeGenerationResult

```python
{
    "title": "番茄鸡蛋汤",
    "title_zh": "番茄鸡蛋汤",
    "description": "这是一道传统的番茄鸡蛋汤。",
    "ingredients": [
        {"name": "鸡蛋", "quantity": "2", "unit": "个", "notes": "建议打散或单独处理后再合入主菜。"},
        {"name": "番茄", "quantity": "1", "unit": "个", "notes": "适合先切块，烹饪时可利用其自然出汁。"},
        {"name": "葱", "quantity": "1", "unit": "根", "notes": "通常用于提香，建议切小备用。"}
    ],
    "steps": [
        {
            "instruction": "先打散鸡蛋，番茄切块；起锅下油爆香葱段，下番茄翻炒出汁；加入清汤烧开，下蛋花搅散；调味即可。",
            "duration_minutes": 0,
            "tips": "以下流程说明直接根据 ai_training_data 的 input_description 整理。"
        }
    ],
    "tips": "已根据训练库中的相关做法整理流程，建议在约 30 分钟内按顺序完成。",
    "nutrition": {
        "calories_per_serving": 240,
        "protein_g": 12,
        "fat_g": 10,
        "carbs_g": 25
    }
}
```

## 配置更新

不再需要以下配置：
- `openai_api_key`
- `anthropic_api_key`
- `settings.ai_model`
- `settings.vision_model`

仅需确保 `SUPABASE_URL` 和 `SUPABASE_KEY` 配置正确。
