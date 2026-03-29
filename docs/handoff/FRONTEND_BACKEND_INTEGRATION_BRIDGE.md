# 拍立食 H5 前后端联调桥接文档

更新时间：2026-03-29
适用范围：当前 H5 总装页、阶段页、拆分页，与 `backend/api/routes.py` 中现有接口的首次联调

## 1. 这份文档解决什么问题

当前后端的生图、识图、Supabase 存储链路已经有接口落点，但 H5 主链路仍然是本地静态闭环：

- 前端主要依赖 `sessionStorage`、`window.location` 和占位跳转推进流程
- 当前主流程没有真实 `fetch` 到 `/api/v1`
- 结果页和加载页消费的是本地预置图、query 参数或临时缓存，不是后端返回

因此这份文档的目标不是替代后端开发，而是补齐前端/产品侧原本应该提前定义好的联调约定，让后端同学可以按约定接入。

## 2. 当前前端真实状态

### 2.1 已存在的前端主链路

当前线上入口与正式入口都指向：

- `frontend/index.html`
- `frontend/vercel.json`
- `frontend/prototype/Chinese/完整App-总装_真实阶段直连版.html`

主链路大致是：

1. 引导/登录
2. Nexus
3. 拍摄
4. 分子重构台
5. 加载过渡
6. 结果页
7. 保存到档案馆

### 2.2 当前仍然是“前端闭环”的位置

- `frontend/prototype/Chinese/拍摄.html`
  - 当前只负责相机采集和本地预览，没有上传 API。
- `frontend/prototype/Chinese/分子重构台.html`
  - 当前只把用户选择写入 `sessionStorage` 的 `molecularReconstructSelection`，然后跳转到加载页。
- `frontend/prototype/Chinese/加载过渡.html`
  - 当前只读取 `molecularReconstructSelection`，并使用本地 fallback 图片或 `generatedBoardPreview` 做预览。
  - 当前没有真实请求后端生成接口。
- `frontend/prototype/Chinese/艺术的诞生.html`
  - 当前只消费 query 中的 `boardPreview`、`sessionStorage.generatedBoardPreview` 或默认图。
  - 当前没有消费完整的后端生成结果。

### 2.3 阶段页和总装页中的历史占位

阶段页内部仍然存在明确的占位路由和说明：

- `frontend/prototype/Chinese/完整App-阶段2.html`
  - `loading-placeholder`
  - `placeholder-archive`
  - `placeholder-profile`
- `frontend/prototype/Chinese/完整App-阶段3.html`
  - `placeholder-camera`
  - `placeholder-nexus`
  - `placeholder-archive`
- `frontend/prototype/Chinese/完整App-阶段4.html`
  - `placeholder-nexus`
  - `placeholder-camera`
  - `placeholder-auth`

结论：后端“接不上”的核心原因不是接口不存在，而是前端此前没有把正式的联调入口、状态消费规则和错误处理约定提前定下来。

## 3. 当前后端已存在的可用接口

以 `backend/main.py` 的 `API_PREFIX=/api/v1` 为准，当前实际可用于 H5 主链路的接口有：

- `POST /api/v1/recognize/image`
- `POST /api/v1/generate/from-image`
- `POST /api/v1/generate/recipe`
- `POST /api/v1/archives`
- `GET /api/v1/archives`

其中主链路最重要的是：

### 3.1 `POST /api/v1/generate/from-image`

用途：

- 输入图片
- 后端做识图
- 后端生成菜谱
- 后端生成成品图
- 后端把生成图存到 Supabase Storage
- 返回结果页可直接消费的数据

请求体：

```json
{
  "image_base64": "data:image/jpeg;base64,..."
}
```

或：

```json
{
  "image_url": "https://..."
}
```

当前响应结构要点：

```json
{
  "success": true,
  "recipe": {
    "title": "English title",
    "title_zh": "中文菜名",
    "description": "一句简介",
    "ingredients": [],
    "steps": [],
    "tips": "整道菜提示",
    "nutrition": {},
    "image_prompt": "生成图提示词"
  },
  "title": "中文菜名",
  "summary": "一句简介",
  "steps": [],
  "recognition": {
    "ingredients": [],
    "cooking_method": "煎/炒/烤等",
    "nutrition_notes": "",
    "allergen_warning": []
  },
  "imageUrl": "https://...",
  "boardPreview": "https://...",
  "storagePath": "generated/xxx.png"
}
```

### 3.2 `POST /api/v1/generate/recipe`

用途：

- 输入“分子重构台”中人工确认后的食材、技法、口味、工具
- 后端直接生成菜谱
- 后端可同步生成成品图并存储

当前后端支持的请求字段：

```json
{
  "ingredients": [
    "鸡胸肉",
    "圣女果",
    "罗勒"
  ],
  "cooking_technique": "煎",
  "technique": "煎",
  "flavor_profile": "家常",
  "tastes": ["鲜", "微酸"],
  "spice_level": 3,
  "max_time": 30,
  "equipment": ["平底锅"],
  "tools": ["平底锅"]
}
```

说明：

- `cooking_technique` 和 `technique` 当前都可传，后端已有兼容。
- `equipment` 和 `tools` 当前都可传，后端已有兼容。
- `ingredients` 当前后端既支持字符串数组，也兼容对象数组中的 `name` 字段。

响应结构与 `generate/from-image` 基本一致，但通常不带 `recognition`。

### 3.3 `POST /api/v1/archives`

用途：

- 在结果页点击“保存到档案馆”时，把当前作品写入 Supabase

请求体：

```json
{
  "user_id": "frontend-demo-user",
  "title": "低温慢煎鸡胸佐香草番茄",
  "recipe_id": null,
  "generation_log_id": null,
  "cover_image_url": "https://...",
  "is_shared": false
}
```

当前响应：

```json
{
  "success": true,
  "archive": {
    "id": "...",
    "user_id": "frontend-demo-user",
    "title": "低温慢煎鸡胸佐香草番茄",
    "cover_image_url": "https://..."
  }
}
```

## 4. 前端侧正式约定

本节是给后端同学联调时使用的“前端消费合同”。

### 4.1 前端正式输入源

#### A. 图片驱动链路

适用页面：

- `拍摄.html`
- `加载过渡.html`

正式约定：

- 拍摄页最终要输出一个可提交给后端的图片源
- 推荐优先使用 `image_base64`
- 如果后端先上传中转图，也可以使用 `image_url`

前端约定缓存键：

- `capturedImageDataUrl`
  - 拍摄页产出后的图片 data URL

#### B. 用户确认驱动链路

适用页面：

- `分子重构台.html`
- `加载过渡.html`

正式约定：

- `分子重构台.html` 继续保留现有 `molecularReconstructSelection`
- 但这个缓存只代表“用户输入”，不代表“生成结果”

建议结构：

```json
{
  "ingredients": [
    {
      "name": "鸡胸肉",
      "count": 2,
      "unit": "块",
      "included": true
    }
  ],
  "technique": "煎",
  "tools": ["平底锅"],
  "tastes": ["鲜", "微酸"]
}
```

### 4.2 前端正式结果缓存

从这份文档起，结果页和保存动作统一消费同一个结果缓存键：

- `generatedRecipeResult`

建议结构：

```json
{
  "success": true,
  "title": "低温慢煎鸡胸佐香草番茄",
  "summary": "一句简介",
  "steps": [],
  "imageUrl": "https://...",
  "boardPreview": "https://...",
  "storagePath": "generated/xxx.png",
  "recipe": {},
  "recognition": {}
}
```

兼容性要求：

- 结果页优先读取 `generatedRecipeResult`
- 若 `generatedRecipeResult.boardPreview` 存在，则同步写入旧键 `generatedBoardPreview`
- 旧键只作为过渡兼容，后续不应再作为主数据源

### 4.3 页面级消费规则

#### 拍摄页

职责：

- 采集图片
- 输出 `capturedImageDataUrl`
- 不负责解释生成结果

#### 分子重构台

职责：

- 收集用户确认后的食材、技法、工具、味型
- 输出 `molecularReconstructSelection`
- 不负责生成菜谱

#### 加载过渡页

职责：

- 读取 `capturedImageDataUrl` 或 `molecularReconstructSelection`
- 触发真实 API
- 接收响应
- 写入 `generatedRecipeResult`
- 跳转结果页

调用约定：

- 如果有图片输入，优先调用 `POST /api/v1/generate/from-image`
- 如果只有食材确认数据，调用 `POST /api/v1/generate/recipe`

#### 结果页

职责：

- 只消费 `generatedRecipeResult`
- 不再自行拼假数据
- 仅在兼容期读取 `generatedBoardPreview`

#### 档案馆保存动作

职责：

- 从 `generatedRecipeResult` 读取 `title`、`imageUrl` 或 `boardPreview`
- 调用 `POST /api/v1/archives`

## 5. 明确分工边界

### 前端/UI/PM 侧应补齐

- 主链路页面与后端接口的映射关系
- 请求字段命名
- 响应字段消费规则
- `sessionStorage` 主键定义
- 错误态和空态约定
- 结果页与档案馆的字段来源说明

### 后端/API/Supabase 侧应负责

- 接口本身可用
- 响应字段稳定
- CORS 放通实际联调域名
- 图片生成和 Supabase 存储成功
- 线上可访问的 API Base URL

### 不应再互相混淆

- 前端不替后端写 Supabase 存储逻辑
- 后端不需要猜前端该消费哪个字段
- 双方都不再用“先本地拼一个看看”代替正式联调协议

## 6. 当前联调阻塞项

当前最明确的阻塞有 3 个：

### 6.1 前端没有真实 API 入口

现状：

- 当前 H5 主链路没有正式 `fetch` 到 `/api/v1`

影响：

- 后端做完也没有地方被调用

### 6.2 前端没有正式结果对象

现状：

- 当前加载页和结果页消费的是零散的 query、旧缓存键、本地图片兜底

影响：

- 后端返回了结果，也没有统一的数据落点

### 6.3 后端 CORS 目前只允许本地调试域名

当前配置仅包含：

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:8080`

如果要让当前 Vercel H5 联调，后端同学需要把真实前端域名加入 `CORS_ORIGINS`。

## 7. 推荐的最小联调方案

第一阶段只接通“拍摄/重构 -> 加载 -> 结果 -> 保存档案”主链路，不碰社区、商城、训练导出。

### 方案 A：图片优先链路

1. 拍摄页输出 `capturedImageDataUrl`
2. 加载页读取该值并请求 `POST /api/v1/generate/from-image`
3. 响应写入 `generatedRecipeResult`
4. 结果页消费 `generatedRecipeResult`
5. 点击保存时调用 `POST /api/v1/archives`

适合：

- 后端同学已经把识图 + 生图 + 存储打通

### 方案 B：重构台优先链路

1. 分子重构台继续输出 `molecularReconstructSelection`
2. 加载页把它转换成 `POST /api/v1/generate/recipe` 的请求体
3. 响应写入 `generatedRecipeResult`
4. 结果页消费 `generatedRecipeResult`
5. 点击保存时调用 `POST /api/v1/archives`

适合：

- 当前先不接拍摄识图
- 先把人工确认后的食材生成链路接通

## 8. 联调前必须确认的配置

后端同学需要提供：

- 可访问的 API Base URL
- 当前部署环境是否能被前端访问
- 是否已把 Vercel 域名加入 `CORS_ORIGINS`
- Supabase bucket 是否为 `instant-food`

前端联调时统一假定：

- 接口前缀为 `/api/v1`
- 结果页主图字段优先级：`imageUrl` -> `boardPreview`
- 保存档案封面字段优先级：`imageUrl` -> `boardPreview`

## 9. 安全与密钥要求

以下内容不允许出现在前端页面中：

- `SUPABASE_SERVICE_ROLE_KEY`
- Gemini 服务端密钥

前端最多只应该拿到：

- 公开可访问的 API Base URL
- 如确有需要，且架构允许时，再单独评估是否使用 Supabase anon key

## 10. 给后端同学的对接口径

可以直接同步给后端同学：

1. H5 接不上不是因为你的接口一定有问题，而是当前前端主链路还没正式 API 化。
2. 前端这边现在已把主链路的输入、输出、缓存键、页面消费规则定下来了。
3. 你接入时只需要对齐这几个接口：
   - `POST /api/v1/generate/from-image`
   - `POST /api/v1/generate/recipe`
   - `POST /api/v1/archives`
4. 如果你要给 Vercel 上的 H5 联调，请把真实前端域名加入 `CORS_ORIGINS`。
5. 前端主结果对象从现在开始统一叫 `generatedRecipeResult`，不要再依赖零散临时键。

## 11. 这份文档之后的前端任务

前端侧下一步真正需要做的，不是重写后端，而是：

1. 在加载过渡页接入真实 API 调用
2. 在结果页改为消费 `generatedRecipeResult`
3. 在保存动作接入 `POST /api/v1/archives`
4. 在正式入口回归后，补做 H5 验收和归档

