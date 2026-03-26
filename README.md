# 拍立食 Instant Food

拍立食是一个围绕「拍照识别食物 + 健康信息反馈 + 轻社交表达」构建的课程项目仓库。当前仓库以 H5 原型、视觉素材、产品文档和后续小程序/后端结构预留为主。

## 当前状态

- 当前可直接查看的主要成果是 H5 原型，位于 `frontend/prototype/`
- 正式落地目标是微信小程序，不再以 React/Vite Web 应用作为最终交付形态
- 仓库已同步到 GitHub，二进制资源通过 Git LFS 管理

## 主要入口

- 中文总装原型：`frontend/prototype/Chinese/完整App-总装.html`
- 中文分阶段原型：`frontend/prototype/Chinese/完整App-阶段1.html` 到 `frontend/prototype/Chinese/完整App-阶段4.html`
- 英文原型目录：`frontend/prototype/English/`
- 背景素材目录：`frontend/assets/backgrounds/`

## 目录结构

```text
frontend/
  assets/        页面直接引用的图片素材
  prototype/     H5 原型页面（中英双版本）
  miniprogram/   后续微信小程序前端目录

backend/
  api/           后端接口预留
  database/      数据库脚本与结构预留

docs/
  architecture/  技术架构、协作基线
  backend/       数据模型与接口文档
  handoff/       交接资料
  planning/      项目范围与任务板
  presentations/ 汇报材料
  reference/     课程与参考资料
  ui/            UI 风格基线

tests/
  visual/        页面自检截图与视觉验证资料

archive/         历史归档资料
scripts/         辅助脚本
tmp/             临时文件目录
```

## 本地查看原型

不要直接双击 HTML。请在项目根目录启动一个本地静态服务器，再通过浏览器访问。

```powershell
cd frontend/prototype/Chinese
python -m http.server 8000
```

然后打开：

- `http://localhost:8000/完整App-总装.html`

这样可以避免本地 `file://` 打开时的资源路径问题，尤其是图片不显示的问题。

## 克隆与资源说明

仓库中的 `mp4`、`png`、`jpg`、`pdf`、`docx` 通过 Git LFS 管理。首次克隆后建议执行：

```powershell
git lfs install
git lfs pull
```

否则你可能只能拿到指针文件，无法正常查看视频、图片或文档资源。

## 建议优先阅读

- `docs/architecture/TECH_ARCHITECTURE.md`
- `docs/architecture/TEAM_SYNC_PACKAGE.md`
- `docs/planning/PROJECT_SCOPE.md`
- `docs/ui/UI_STYLE_BASELINE.md`
- `docs/README.md`

## 仓库说明

- `.playwright-cli/` 和 `archive/browser-profiles/` 这类本机运行缓存已排除，不会进入版本库
- `output/` 和 `tmp/` 用于开发过程中的临时产物，不视为正式交付目录
- `archive/` 中保留历史资料，默认不作为当前开发主目录
