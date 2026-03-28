# 拍立食 Supabase 后端数据中心设计方案

## 1. 目标概述

### 1.1 核心目标
1. **数据存储中心**：将食谱数据存入 Supabase，用作 AI prompt 训练数据
2. **AI 食谱生成**：接入 API Key 后，通过数据训练在用户拍照后生成合适的食谱

### 1.2 技术选型
- **数据库**：Supabase (PostgreSQL)
- **后端框架**：FastAPI + Python
- **AI 集成**：支持 OpenAI GPT-4 Vision / Claude / 本地模型
- **向量搜索**：Supabase pgvector (可选，用于语义搜索)

---

## 2. Supabase 项目配置

### 2.1 创建 Supabase 项目
1. 访问 https://supabase.com 创建新项目
2. 获取以下凭证：
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

### 2.2 环境变量配置
创建 `backend/.env` 文件：
```env
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI API 配置
OPENAI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-4o  # 或 gpt-4-turbo, claude-3-opus 等

# 应用配置
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 3. 数据库架构设计

### 3.1 核心数据表

#### 3.1.1 `recipes` - 食谱主表
```sql
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    title_zh VARCHAR(255),
    description TEXT,
    description_zh TEXT,
    cuisine_type VARCHAR(100),  -- 川菜, 粤菜, 西餐等
    meal_type VARCHAR(50),     -- 早餐, 午餐, 晚餐, 小食
    difficulty VARCHAR(20),     -- easy, medium, hard
    prep_time_minutes INT,
    cook_time_minutes INT,
    servings INT DEFAULT 1,
    calories_per_serving INT,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_published BOOLEAN DEFAULT false,
    is_ai_generated BOOLEAN DEFAULT false,
    source VARCHAR(100)  -- manual, ai_generated, imported
);
```

#### 3.1.2 `ingredients` - 食材表
```sql
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    name_zh VARCHAR(255),
    category VARCHAR(100),     -- 肉类, 蔬菜, 主食, 调料等
    subcategory VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'g',
    calories_per_100g DECIMAL(10,2),
    protein_per_100g DECIMAL(10,2),
    fat_per_100g DECIMAL(10,2),
    carbs_per_100g DECIMAL(10,2),
    is_allergen BOOLEAN DEFAULT false,
    allergen_types TEXT[],     -- 过敏原类型数组
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.3 `recipe_ingredients` - 食谱食材关联表
```sql
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id),
    ingredient_name VARCHAR(255),  -- 备用食材名
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50),
    notes TEXT,  -- 如 "切丁", "去皮"
    is_optional BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.4 `recipe_steps` - 食谱步骤表
```sql
CREATE TABLE recipe_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    instruction TEXT NOT NULL,
    instruction_zh TEXT,
    duration_minutes INT,
    image_url TEXT,
    tips TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.5 `cooking_techniques` - 烹饪技法表
```sql
CREATE TABLE cooking_techniques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description TEXT,
    equipment VARCHAR(100),  -- 锅具要求
    difficulty VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.6 `flavor_profiles` - 风味档案表
```sql
CREATE TABLE flavor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    base_sauces TEXT[],       -- 基础酱料
    spices TEXT[],            -- 香料
    cooking_methods TEXT[],   -- 烹饪方式
    taste_tags TEXT[],        -- 甜, 咸, 酸, 辣, 苦, 鲜
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.7 `user_preferences` - 用户偏好表
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    dietary_restrictions TEXT[],  -- 素食, 无麸质等
    allergies TEXT[],
    preferred_cuisines TEXT[],
    disliked_ingredients TEXT[],
    preferred_spice_level INT,    -- 1-5 辣度偏好
    calorie_target INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.8 `ai_training_data` - AI 训练数据表
```sql
CREATE TABLE ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    prompt_template TEXT NOT NULL,
    input_description TEXT,  -- 食材描述输入
    expected_output TEXT,     -- 期望的食谱输出
    metadata JSONB,           -- 额外元数据
    quality_score DECIMAL(3,2),  -- 质量评分 0-1
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3.1.9 `generation_logs` - 生成日志表
```sql
CREATE TABLE generation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    input_image_url TEXT,
    recognized_ingredients TEXT[],
    user_preferences JSONB,
    generated_recipe JSONB,
    ai_model_used VARCHAR(100),
    generation_time_ms INT,
    quality_rating INT,        -- 用户评分 1-5
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 4. API 接口设计

### 4.1 食谱管理 API

```
POST   /api/recipes                    # 创建食谱
GET    /api/recipes                    # 获取食谱列表
GET    /api/recipes/{id}               # 获取单个食谱
PUT    /api/recipes/{id}               # 更新食谱
DELETE /api/recipes/{id}               # 删除食谱
POST   /api/recipes/bulk-import        # 批量导入食谱
```

### 4.2 AI 生成 API

```
POST   /api/generate/recipe            # 根据食材生成食谱
POST   /api/generate/from-image        # 从图片生成食谱（拍照后）
POST   /api/generate/alternatives      # 生成替代食谱
```

### 4.3 食材管理 API

```
POST   /api/ingredients                 # 添加食材
GET    /api/ingredients                # 获取食材列表
GET    /api/ingredients/search         # 搜索食材
```

### 4.4 训练数据 API

```
GET    /api/training/export             # 导出训练数据
POST   /api/training/log               # 记录生成日志
GET    /api/training/quality-report    # 质量报告
```

---

## 5. AI 集成架构

### 5.1 Prompt 工程设计

#### 5.1.1 食谱生成 Prompt 模板
```
你是一位专业的中餐厨师。请根据以下食材和偏好生成一道美味的食谱。

食材: {ingredients_list}
用户偏好:
- 烹饪技法: {cooking_technique}
- 风味档案: {flavor_profile}
- 辣度: {spice_level}/5
- 时间限制: {max_time}分钟

要求:
1. 食谱要有创意但实用
2. 步骤清晰易操作
3. 包含营养信息和过敏原提醒
4. 适合中国家庭厨房

请以JSON格式输出:
{
  "title": "食谱名称",
  "title_zh": "中文名",
  "description": "简介",
  "ingredients": [{"name": "食材", "quantity": "用量", "unit": "单位"}],
  "steps": [{"instruction": "步骤", "duration": 分钟}],
  "tips": "小贴士",
  "nutrition": {"calories": 卡路里, "protein": "蛋白质克数"}
}
```

#### 5.1.2 图片识别 Prompt 模板
```
请分析这张食物图片，识别出主要的食材成分。

要求:
1. 列出所有可见的食材
2. 估计每种食材的大致用量
3. 识别烹饪方式（如炒、煮、蒸、烤等）
4. 评估这道菜的营养特点

请以JSON格式输出:
{
  "ingredients": [{"name": "食材名", "estimated_quantity": "估计用量", "confidence": 0.0-1.0}],
  "cooking_method": "烹饪方式",
  "nutrition_notes": "营养特点",
  "allergen_warning": ["过敏原列表"]
}
```

### 5.2 模型选择建议

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 图片识别 | GPT-4 Vision / Claude 3 Vision | 多模态能力强 |
| 食谱生成 | GPT-4o / Claude 3.5 Sonnet | 创意+准确性平衡 |
| 本地部署 | LLaVA + 开源LLM | 隐私/离线需求 |

---

## 6. 实施步骤

### Phase 1: 数据基础设施 (第1-2周)
- [ ] 创建 Supabase 项目
- [ ] 配置数据库表结构
- [ ] 设置 Row Level Security (RLS)
- [ ] 配置存储桶 (图片)
- [ ] 编写数据导入脚本

### Phase 2: API 开发 (第3-4周)
- [ ] 搭建 FastAPI 项目结构
- [ ] 实现食谱 CRUD API
- [ ] 实现食材管理 API
- [ ] 连接 Supabase 数据库

### Phase 3: AI 集成 (第5-6周)
- [ ] 集成 OpenAI/Claude API
- [ ] 实现图片识别功能
- [ ] 实现食谱生成功能
- [ ] 构建 Prompt 工程体系

### Phase 4: 训练数据管道 (第7-8周)
- [ ] 构建训练数据集
- [ ] 实现质量评估
- [ ] 导出训练数据
- [ ] 集成反馈循环

### Phase 5: 测试与优化 (第9-10周)
- [ ] 功能测试
- [ ] 性能优化
- [ ] 安全审计
- [ ] 文档完善

---

## 7. 质量保证

### 7.1 数据质量
- 食谱必须经过审核才能发布
- AI 生成的内容需要人工校验
- 定期清理低质量数据

### 7.2 输出质量
- 用户可以对生成结果评分
- 记录生成日志用于分析
- 持续优化 Prompt 模板

---

## 8. 成本估算

### 8.1 Supabase 成本
| 层级 | 价格 | 适用场景 |
|------|------|---------|
| Free | $0 | 开发/小规模 |
| Pro | $25/月 | 生产环境 |

### 8.2 AI API 成本 (参考)
- GPT-4o: $5/1M tokens (输入), $15/1M tokens (输出)
- GPT-4 Vision: $21.43/1M images

---

## 9. 后续扩展

### 9.1 向量搜索 (可选)
使用 pgvector 实现语义相似食谱搜索

### 9.2 微调模型
使用收集的训练数据微调开源模型

### 9.3 用户生成内容
- 社区分享功能
- 用户评分和评论
- 个性化推荐
