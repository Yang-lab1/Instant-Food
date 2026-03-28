-- ============================================
-- 生成结果扩展: 图片、食材图谱、流程教学
-- 说明:
-- 1. 复用现有 generation_logs 表，不新建重复表
-- 2. 用于存储一次 AI 生成对应的图片结果与教学结果
-- 3. 兼容 Supabase SQL Editor 直接执行
-- ============================================

ALTER TABLE public.generation_logs
ADD COLUMN IF NOT EXISTS recipe_id UUID REFERENCES public.recipes(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS generated_image_url TEXT,
ADD COLUMN IF NOT EXISTS generated_image_urls TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS generated_image_prompt TEXT,
ADD COLUMN IF NOT EXISTS ingredient_atlas JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS teaching_steps JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS teaching_summary JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS teaching_text TEXT,
ADD COLUMN IF NOT EXISTS generation_type VARCHAR(50) DEFAULT 'image_to_recipe',
ADD COLUMN IF NOT EXISTS generation_status VARCHAR(30) DEFAULT 'completed',
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

COMMENT ON COLUMN public.generation_logs.recipe_id IS '关联到 recipes 主表的食谱 ID';
COMMENT ON COLUMN public.generation_logs.generated_image_url IS '本次生成主图 URL';
COMMENT ON COLUMN public.generation_logs.generated_image_urls IS '本次生成的多张图片 URL 列表';
COMMENT ON COLUMN public.generation_logs.generated_image_prompt IS '用于生成图片的提示词';
COMMENT ON COLUMN public.generation_logs.ingredient_atlas IS '图谱式食材介绍 JSON 数组';
COMMENT ON COLUMN public.generation_logs.teaching_steps IS '做法流程教学 JSON 数组';
COMMENT ON COLUMN public.generation_logs.teaching_summary IS '上手提醒/总结卡片 JSON 数组';
COMMENT ON COLUMN public.generation_logs.teaching_text IS '完整文字教学说明';
COMMENT ON COLUMN public.generation_logs.generation_type IS '生成类型: image_to_recipe / text_to_recipe / image_generation';
COMMENT ON COLUMN public.generation_logs.generation_status IS '生成状态: pending / completed / failed';

CREATE INDEX IF NOT EXISTS idx_generation_logs_recipe
ON public.generation_logs(recipe_id);

CREATE INDEX IF NOT EXISTS idx_generation_logs_generation_type
ON public.generation_logs(generation_type);

CREATE INDEX IF NOT EXISTS idx_generation_logs_generation_status
ON public.generation_logs(generation_status);

CREATE INDEX IF NOT EXISTS idx_generation_logs_ingredient_atlas_gin
ON public.generation_logs
USING GIN (ingredient_atlas);

CREATE INDEX IF NOT EXISTS idx_generation_logs_teaching_steps_gin
ON public.generation_logs
USING GIN (teaching_steps);

CREATE INDEX IF NOT EXISTS idx_generation_logs_teaching_summary_gin
ON public.generation_logs
USING GIN (teaching_summary);

CREATE OR REPLACE FUNCTION public.update_generation_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_generation_logs_updated_at ON public.generation_logs;

CREATE TRIGGER update_generation_logs_updated_at
BEFORE UPDATE ON public.generation_logs
FOR EACH ROW
EXECUTE FUNCTION public.update_generation_logs_updated_at();

-- 示例数据结构:
-- ingredient_atlas:
-- [
--   {
--     "name": "番茄",
--     "amount": "2个",
--     "role": "主蔬菜",
--     "action": "建议切块备用",
--     "intro": "番茄能提供酸甜味和汁水。"
--   }
-- ]
--
-- teaching_steps:
-- [
--   {
--     "step_no": 1,
--     "title": "备料阶段",
--     "instruction": "番茄切块，鸡蛋打散。",
--     "duration": "3 分钟",
--     "tip": "先把材料准备好，下锅会更顺。"
--   }
-- ]
--
-- teaching_summary:
-- [
--   { "label": "原材料", "value": "3 项已识别" },
--   { "label": "节奏", "value": "4 步完成一餐" },
--   { "label": "时长", "value": "约 12 分钟" }
-- ]
