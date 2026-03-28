# 本地启动命令

## 1. 重启后端
在一个终端窗口里运行：

```bash
cd /Users/erzhuonie/Documents/GitHub/Instant-Food/backend
../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8011
```

## 2. 重启前端
在另一个终端窗口里运行：

```bash
cd /Users/erzhuonie/Documents/GitHub/Instant-Food/frontend/app
npm run dev -- --host 127.0.0.1 --port 5173
```

## 3. 打开地址

- 前端页面: `http://127.0.0.1:5173/`
- 后端文档: `http://127.0.0.1:8011/docs`
- 健康检查: `http://127.0.0.1:8011/api/v1/health`

## 4. 如果后端端口被占用
先执行：

```bash
kill -9 $(lsof -tiTCP:8011 -sTCP:LISTEN)
```

再重新运行后端命令。

## 5. 如果前端端口被占用
先执行：

```bash
kill -9 $(lsof -tiTCP:5173 -sTCP:LISTEN)
```

再重新运行前端命令。
