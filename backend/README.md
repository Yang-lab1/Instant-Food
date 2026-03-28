# 拍立食后端 - 快速开始指南

## 🚀 快速启动

### 1. 前置要求
- Python 3.10-3.13
- Supabase 账号
- OpenAI API Key (可选，用于 AI 功能)

### 2. 配置环境

```bash
cd backend

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入你的配置
nano .env
```

### 3. 创建 Supabase 项目

1. 访问 [supabase.com](https://supabase.com) 创建新项目
2. 获取以下凭证：
   - Project URL
   - `anon` public key
   - `service_role` secret key

3. 在 Supabase SQL Editor 中运行数据库迁移：
   - 打开 `database/migrations/001_initial_schema.sql`
   - 复制内容到 Supabase SQL Editor
   - 点击运行

### 4. 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果你使用的是 `Python 3.13`，请确保先拉取最新依赖版本。旧版 `pydantic` 会尝试本地编译 `pydantic-core`，在未安装 Rust 工具链时容易报错。

如果你使用 Gemini，建议在 `.env` 中把 `AI_MODEL` 和 `VISION_MODEL` 设为 `gemini-2.5-flash`，避免旧模型名失效导致 `generateContent` 返回 404。

### 5. 启动服务

```bash
# 开发模式
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

---

## 📚 API 端点

### AI 功能

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/recognize/image` | 识别图片中的食材 |
| POST | `/api/v1/generate/recipe` | 根据食材生成食谱 |
| POST | `/api/v1/generate/from-image` | 从图片生成完整食谱 |
| GET | `/api/v1/ai/status` | AI 服务状态 |

### 食谱管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/recipes` | 获取食谱列表 |
| GET | `/api/v1/recipes/{id}` | 获取食谱详情 |
| POST | `/api/v1/recipes` | 创建食谱 |
| DELETE | `/api/v1/recipes/{id}` | 删除食谱 |

### 其他

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/ingredients` | 获取食材列表 |
| GET | `/api/v1/ingredients/search?q=...` | 搜索食材 |
| GET | `/api/v1/flavor-profiles` | 获取风味档案 |
| GET | `/api/v1/cooking-techniques` | 获取烹饪技法 |
| GET | `/api/v1/training/export` | 导出训练数据 |

---

## 💡 使用示例

### 识别图片中的食材

```bash
curl -X POST "http://localhost:8000/api/v1/recognize/image" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/food.jpg"}'
```

### 根据食材生成食谱

```bash
curl -X POST "http://localhost:8000/api/v1/generate/recipe" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["番茄", "鸡蛋", "葱"],
    "cooking_technique": "炒",
    "flavor_profile": "家常",
    "spice_level": 1
  }'
```

### 创建食谱

```bash
curl -X POST "http://localhost:8000/api/v1/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "番茄炒蛋",
    "title_zh": "番茄炒蛋",
    "description": "经典家常菜",
    "cuisine_type": "中餐",
    "meal_type": "午餐",
    "difficulty": "easy",
    "prep_time_minutes": 5,
    "cook_time_minutes": 10,
    "servings": 2,
    "ingredients": [
      {"name": "番茄", "quantity": "2", "unit": "个"},
      {"name": "鸡蛋", "quantity": "3", "unit": "个"}
    ],
    "steps": [
      {"instruction": "番茄切块，鸡蛋打散", "duration_minutes": 2},
      {"instruction": "热锅凉油，炒鸡蛋", "duration_minutes": 3},
      {"instruction": "加入番茄翻炒", "duration_minutes": 5}
    ],
    "is_published": true
  }'
```

---

## 🏗️ 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置管理
├── requirements.txt        # Python 依赖
├── .env.example           # 环境变量模板
├── api/
│   ├── __init__.py
│   ├── routes.py           # API 路由
│   └── ai_client.py        # AI 服务客户端
├── database/
│   ├── __init__.py
│   ├── supabase_client.py  # Supabase 客户端
│   └── migrations/
│       └── 001_initial_schema.sql  # 数据库迁移
└── docs/
    └── SUPABASE_BACKEND_DESIGN.md  # 完整设计文档
```

---

## 🔧 配置说明

### 环境变量

| 变量 | 必填 | 描述 |
|------|------|------|
| `SUPABASE_URL` | ✅ | Supabase 项目 URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key |
| `OPENAI_API_KEY` | ❌ | OpenAI API Key (启用 AI 功能) |
| `AI_MODEL` | ❌ | AI 模型，默认 gpt-4o |
| `APP_ENV` | ❌ | 环境，development/production |

---

## 📊 数据库表

| 表名 | 描述 |
|------|------|
| `recipes` | 食谱主表 |
| `ingredients` | 食材表 |
| `recipe_ingredients` | 食谱食材关联 |
| `recipe_steps` | 食谱步骤 |
| `cooking_techniques` | 烹饪技法 |
| `flavor_profiles` | 风味档案 |
| `user_preferences` | 用户偏好 |
| `ai_training_data` | AI 训练数据 |
| `generation_logs` | 生成日志 |
| `archives` | 档案馆 |
| `ingredient_nutrition_master` | 营养数据 |

---

## 🎯 下一步

1. 完成 Supabase 配置和数据库迁移
2. 配置 OpenAI API Key
3. 导入示例食谱数据
4. 测试 AI 生成功能
5. 集成到前端应用
