# 拍立食后端接管执行手册（2026-04-02）

适用场景：后端同学暂时不在，由前端/UI 组临时接管联调、部署、演示链路。

## 1. 当前已完成状态

- 后端已部署到 Vercel（生产别名）：
  - `https://instant-food-backend-api-20260402.vercel.app`
- 健康检查可用：
  - `GET /api/v1/health` 返回 200
  - `GET /api/v1/ai/status` 返回 200
  - `GET /api/v1/ingredients` 返回 200
- CORS 已允许当前前端线上域名：
  - `https://frontend-flame-one-rgedpp5pu4.vercel.app`
- 前端 API bridge 已改为默认连线上后端，不再强依赖手动设置 `apiBaseUrl`。

## 2. 当前状态（已解除阻塞）

- `GEMINI_API_KEY` 更新并重部署后，`POST /api/v1/generate/recipe` 已返回 200。
- 归档写入 `POST /api/v1/archives` 已返回 200。

结论：前后端在线演示链路当前可用，不再是接口或密钥阻塞态。

## 3. 你们现在要做的最小动作

1. 保持 Vercel 项目 `instant-food-backend-api-20260402` 环境变量有效（尤其 `GEMINI_API_KEY`）。
2. 若后续改 key 或改配置，重新部署一次生产环境。
3. 每次部署后回归下面三个接口：
   - `GET /api/v1/health`
   - `GET /api/v1/ai/status`
   - `POST /api/v1/generate/recipe`

## 4. 前端联调用法（已可直接给队友）

默认访问（不带参数）即可连后端：

- `https://frontend-flame-one-rgedpp5pu4.vercel.app`

如需临时切到其他后端，可用：

- `?apiBaseUrl=https://你的后端域名`

例如：

- `https://frontend-flame-one-rgedpp5pu4.vercel.app/?apiBaseUrl=https%3A%2F%2Finstant-food-backend-api-20260402.vercel.app`

## 5. 代码侧关键改动

- `backend/requirements.txt`
  - `supabase==2.6.0`（与当前 `httpx==0.26.0` 兼容）
- `backend/vercel.json`
  - 固定 Python 入口构建与路由
- `backend/index.py`
  - Vercel runtime 入口（导出 FastAPI `app`）
- `frontend/prototype/Chinese/instant-food-api-bridge.js`
  - 默认 API Base URL 指向线上后端
  - 支持 `apiBaseUrl` query 自动写入 storage，跨页面保持一致

## 6. 安全边界

- `SUPABASE_SERVICE_ROLE_KEY`、`GEMINI_API_KEY` 只能放后端环境变量。
- 不允许放到前端代码或公开仓库文档里。
