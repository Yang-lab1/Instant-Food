# 发现与决策

## 需求
- 先做 repo 体检，不直接补丁。
- 前后端一起看，优先删除假数据、旧逻辑、旧模板，而不是继续隐藏。
- 任何 H5 / 前端改动都必须按 `docs/h5_acceptance_standard.md` 验收。
- 每次中等以上修改都要归档验证证据到 `archive/validation/<date>-<topic>`。

## 研究发现
- 当前分支为 `branch—1`，工作区明显是脏的，包含前后端大量已修改和未跟踪文件。
- 正式入口仍是 `frontend/index.html`，实验入口仍是 `frontend/prototype/Chinese/完整App-总装_真实阶段直连版.html`。
- 用户已明确说明 `frontend/拍立食backend(1).zip` 与 `frontend/拍立食backend/` 只可作为参考来源，正式后端以 `backend/` 为准。

## 技术决策
| 决策 | 理由 |
|------|------|
| 先记录基线，再碰代码 | 避免把旧脏改动误记为本轮修改 |
| 优先看 bridge、loading、结果链路和 backend recipe/image 生成逻辑 | 这是当前最可能阻断和回归的链路 |

## 遇到的问题
| 问题 | 解决方案 |
|------|---------|
| 计划技能模板存在编码乱码 | 直接按技能意图自行创建项目内计划文件 |

## 资源
- `AGENTS.md`
- `docs/h5_acceptance_standard.md`
- 用户列出的重点文件和最近验证归档

## 视觉/浏览器发现
- 暂无，待开始浏览器验收后持续补充。
