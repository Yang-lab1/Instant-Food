-- 拍立食 Supabase 数据库初始化脚本
-- 运行此脚本在 Supabase SQL Editor 中创建所有表

-- ============================================
-- 启用 UUID 扩展
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 表 1: 食谱主表 recipes
-- ============================================
CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    title_zh VARCHAR(255),
    description TEXT,
    description_zh TEXT,
    cuisine_type VARCHAR(100),  -- 川菜, 粤菜, 西餐等
    meal_type VARCHAR(50),      -- 早餐, 午餐, 晚餐, 小食
    difficulty VARCHAR(20) DEFAULT 'medium',  -- easy, medium, hard
    prep_time_minutes INT DEFAULT 0,
    cook_time_minutes INT DEFAULT 0,
    servings INT DEFAULT 1,
    calories_per_serving INT,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_published BOOLEAN DEFAULT false,
    is_ai_generated BOOLEAN DEFAULT false,
    source VARCHAR(100) DEFAULT 'manual',  -- manual, ai_generated, imported
    metadata JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);
CREATE INDEX IF NOT EXISTS idx_recipes_published ON recipes(is_published);
CREATE INDEX IF NOT EXISTS idx_recipes_created ON recipes(created_at DESC);

-- ============================================
-- 表 2: 食材表 ingredients
-- ============================================
CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    name_zh VARCHAR(255),
    category VARCHAR(100),      -- 肉类, 蔬菜, 主食, 调料等
    subcategory VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'g',
    calories_per_100g DECIMAL(10,2),
    protein_per_100g DECIMAL(10,2),
    fat_per_100g DECIMAL(10,2),
    carbs_per_100g DECIMAL(10,2),
    fiber_per_100g DECIMAL(10,2),
    sodium_per_100g DECIMAL(10,2),
    is_allergen BOOLEAN DEFAULT false,
    allergen_types TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ingredients_category ON ingredients(category);
CREATE INDEX IF NOT EXISTS idx_ingredients_allergen ON ingredients(is_allergen);
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_ingredients_name_zh ON ingredients(name_zh);

-- ============================================
-- 表 3: 食谱食材关联表 recipe_ingredients
-- ============================================
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
    ingredient_name VARCHAR(255) NOT NULL,  -- 备用食材名
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'g',
    notes TEXT,  -- 如 "切丁", "去皮"
    is_optional BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ingredient ON recipe_ingredients(ingredient_id);

-- ============================================
-- 表 4: 食谱步骤表 recipe_steps
-- ============================================
CREATE TABLE IF NOT EXISTS recipe_steps (
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

-- 索引
CREATE INDEX IF NOT EXISTS idx_recipe_steps_recipe ON recipe_steps(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_steps_order ON recipe_steps(recipe_id, step_number);

-- ============================================
-- 表 5: 烹饪技法表 cooking_techniques
-- ============================================
CREATE TABLE IF NOT EXISTS cooking_techniques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description TEXT,
    equipment VARCHAR(100),  -- 锅具要求
    difficulty VARCHAR(20) DEFAULT 'medium',
    icon_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name)
);

-- ============================================
-- 表 6: 风味档案表 flavor_profiles
-- ============================================
CREATE TABLE IF NOT EXISTS flavor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description TEXT,
    base_sauces TEXT[] DEFAULT '{}',
    spices TEXT[] DEFAULT '{}',
    cooking_methods TEXT[] DEFAULT '{}',
    taste_tags TEXT[] DEFAULT '{}',  -- 甜, 咸, 酸, 辣, 苦, 鲜
    region VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name)
);

-- ============================================
-- 表 7: 用户偏好表 user_preferences
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    dietary_restrictions TEXT[] DEFAULT '{}',  -- 素食, 无麸质等
    allergies TEXT[] DEFAULT '{}',
    preferred_cuisines TEXT[] DEFAULT '{}',
    disliked_ingredients TEXT[] DEFAULT '{}',
    preferred_spice_level INT DEFAULT 3,  -- 1-5 辣度偏好
    calorie_target INT,
    meal_preferences TEXT[] DEFAULT '{}',
    equipment_available TEXT[] DEFAULT '{}',  -- 可用厨具
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);

-- ============================================
-- 表 8: AI 训练数据表 ai_training_data
-- ============================================
CREATE TABLE IF NOT EXISTS ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    prompt_template TEXT NOT NULL,
    input_description TEXT,
    expected_output TEXT,
    metadata JSONB DEFAULT '{}',
    quality_score DECIMAL(3,2) DEFAULT 0.5,  -- 质量评分 0-1
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_validated BOOLEAN DEFAULT false,
    validator_id VARCHAR(255)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ai_training_recipe ON ai_training_data(recipe_id);
CREATE INDEX IF NOT EXISTS idx_ai_training_quality ON ai_training_data(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_ai_training_validated ON ai_training_data(is_validated);

-- ============================================
-- 表 9: 生成日志表 generation_logs
-- ============================================
CREATE TABLE IF NOT EXISTS generation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    input_image_url TEXT,
    input_image_base64 TEXT,
    recognized_ingredients TEXT[] DEFAULT '{}',
    user_preferences JSONB DEFAULT '{}',
    generated_recipe JSONB DEFAULT '{}',
    ai_model_used VARCHAR(100),
    generation_time_ms INT,
    tokens_used INT,
    cost_usd DECIMAL(10,4),
    quality_rating INT,        -- 用户评分 1-5
    user_feedback TEXT,
    is_saved_to_archive BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_generation_logs_user ON generation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_logs_created ON generation_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_logs_quality ON generation_logs(quality_rating);

-- ============================================
-- 表 10: 档案馆记录表 archives
-- ============================================
CREATE TABLE IF NOT EXISTS archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL,
    generation_log_id UUID REFERENCES generation_logs(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    cover_image_url TEXT,
    is_shared BOOLEAN DEFAULT false,
    shared_at TIMESTAMP WITH TIME ZONE,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_archives_user ON archives(user_id);
CREATE INDEX IF NOT EXISTS idx_archives_shared ON archives(is_shared);

-- ============================================
-- 表 11: 健康参考数据表 (整合 HEALTH_DATA_MODEL)
-- ============================================
CREATE TABLE IF NOT EXISTS ingredient_nutrition_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fdc_id INTEGER UNIQUE,
    canonical_name VARCHAR(255) NOT NULL,
    display_name_zh VARCHAR(255),
    display_name_en VARCHAR(255),
    category_l1 VARCHAR(100),   -- protein / vegetable / grain / dairy / sauce
    category_l2 VARCHAR(100),
    state VARCHAR(50),         -- raw / cooked / dried
    edible_portion_basis VARCHAR(100) DEFAULT '100g',
    kcal_per_100g DECIMAL(10,2),
    protein_g_per_100g DECIMAL(10,2),
    fat_g_per_100g DECIMAL(10,2),
    saturated_fat_g_per_100g DECIMAL(10,2),
    carb_g_per_100g DECIMAL(10,2),
    fiber_g_per_100g DECIMAL(10,2),
    sugar_g_per_100g DECIMAL(10,2),
    sodium_mg_per_100g DECIMAL(10,2),
    source_dataset VARCHAR(100),
    source_url TEXT,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nutrition_fdc ON ingredient_nutrition_master(fdc_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_category ON ingredient_nutrition_master(category_l1);

-- ============================================
-- Row Level Security (RLS) 配置
-- ============================================

-- 启用 RLS
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE archives ENABLE ROW LEVEL SECURITY;

-- recipes 策略
CREATE POLICY "Allow all reads on recipes" ON recipes FOR SELECT USING (is_published = true);
CREATE POLICY "Allow all inserts on recipes" ON recipes FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow all updates on recipes" ON recipes FOR UPDATE USING (true);
CREATE POLICY "Allow all deletes on recipes" ON recipes FOR DELETE USING (true);

-- user_preferences 策略
CREATE POLICY "Users can view own preferences" ON user_preferences FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own preferences" ON user_preferences FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own preferences" ON user_preferences FOR UPDATE USING (user_id = auth.uid()::text);

-- generation_logs 策略
CREATE POLICY "Users can view own logs" ON generation_logs FOR SELECT USING (user_id = auth.uid()::text OR user_id IS NULL);
CREATE POLICY "Users can insert own logs" ON generation_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own logs" ON generation_logs FOR UPDATE USING (user_id = auth.uid()::text OR user_id IS NULL);

-- archives 策略
CREATE POLICY "Users can view own archives" ON archives FOR SELECT USING (user_id = auth.uid()::text OR is_shared = true);
CREATE POLICY "Users can manage own archives" ON archives FOR ALL USING (user_id = auth.uid()::text);

-- ============================================
-- 函数: 自动更新 updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 触发器
CREATE TRIGGER update_recipes_updated_at BEFORE UPDATE ON recipes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_archives_updated_at BEFORE UPDATE ON archives
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 种子数据: 基础烹饪技法
-- ============================================
INSERT INTO cooking_techniques (name, name_zh, description, equipment, difficulty) VALUES
    ('stir_fry', '炒', '快速翻炒，保持食材脆嫩', '炒锅', 'easy'),
    ('deep_fry', '炸', '油炸至金黄酥脆', '深锅', 'medium'),
    ('steam', '蒸', '利用蒸汽加热', '蒸锅/蒸笼', 'easy'),
    ('boil', '煮', '水煮至熟', '汤锅', 'easy'),
    ('braise', '炖/红烧', '先炒后焖，味道浓郁', '砂锅/炒锅', 'medium'),
    ('roast', '烤', '烤箱或空气炸锅', '烤箱', 'medium'),
    ('grill', '烧烤', '明火或炭火', '烧烤架', 'hard'),
    ('sous_vide', '低温慢煮', '精确控温长时间烹饪', '真空封口机+水浴', 'hard'),
    ('raw', '生食', '直接食用或简单处理', '无', 'easy'),
    ('pickle', '腌制', '醋渍或盐渍', '密封罐', 'medium')
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 种子数据: 风味档案
-- ============================================
INSERT INTO flavor_profiles (name, name_zh, description, base_sauces, spices, cooking_methods, taste_tags, region) VALUES
    ('sichuan', '川菜', '麻辣鲜香', ARRAY['豆瓣酱', '花椒油'], ARRAY['花椒', '干辣椒', '郫县豆瓣'], ARRAY['炒', '红烧'], ARRAY['辣', '麻', '鲜'], '四川'),
    ('cantonese', '粤菜', '清淡鲜美', ARRAY['蚝油', '生抽'], ARRAY['姜', '葱', '蒜'], ARRAY['蒸', '白灼', '炒'], ARRAY['鲜', '甜'], '广东'),
    ('shanghai', '本帮菜', '浓油赤酱', ARRAY['老抽', '黄酒', '白糖'], ARRAY['八角', '桂皮'], ARRAY['红烧', '炒'], ARRAY['甜', '咸', '鲜'], '上海'),
    ('hunan', '湘菜', '香辣酸辣', ARRAY['剁椒'], ARRAY['干辣椒', '豆豉'], ARRAY['炒', '蒸'], ARRAY['辣', '酸'], '湖南'),
    ('japanese', '日式', '清淡调味', ARRAY['酱油', '味醂', '清酒'], ARRAY['芥末', '海苔'], ARRAY['生食', '蒸', '煮'], ARRAY['鲜', '咸', '甜'], '日本'),
    ('korean', '韩式', '辣酱为主', ARRAY['韩式辣酱', '酱油', '芝麻油'], ARRAY['韩式辣椒粉', '大蒜'], ARRAY['炒', '烤', '拌'], ARRAY['辣', '甜', '咸'], '韩国')
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 完成提示
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Create .env file with Supabase credentials';
    RAISE NOTICE '2. Install backend dependencies: pip install -r requirements.txt';
    RAISE NOTICE '3. Run the API server: uvicorn main:app --reload';
END $$;
