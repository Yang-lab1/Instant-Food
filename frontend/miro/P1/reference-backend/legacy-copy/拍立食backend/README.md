# 香疯了 / 拍立食 - 后端

拍冰箱 → 识别食材 → 香了(RAG) or 疯了(LLM) → 正常度打分

## 项目结构

```
xiangfengle/
├── app.py                      # FastAPI 主入口
├── routers/
│   └── recipe.py               # API 路由（3个接口）
├── services/
│   ├── image_recognition.py    # 识图服务（调多模态 LLM）
│   ├── rag_retriever.py        # RAG 检索（香了路线）
│   ├── llm_generator.py        # LLM 生成（疯了路线）
│   └── normality_scorer.py     # 正常度打分（规则层+贝叶斯）
├── models/                     # 模型文件（从 Colab 复制过来）
│   ├── recipes.index           # FAISS 向量索引
│   ├── recipes_meta.json       # 菜谱元数据
│   ├── normality_clf.joblib    # 朴素贝叶斯模型
│   └── normality_vec.joblib    # TF-IDF 向量化器
├── .env.example                # 环境变量模板
├── .gitignore
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 1. 装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API key

# 3. 把 Colab 训练好的模型文件复制到 models/ 目录
# 需要 4 个文件：recipes.index, recipes_meta.json,
# normality_clf.joblib, normality_vec.joblib

# 4. 启动（开发模式）
uvicorn app:app --reload --port 8000

# 5. 打开浏览器访问 API 文档
# http://localhost:8000/docs
```

## API 接口

### POST /api/recognize
上传冰箱照片，识别食材。
- 请求：`multipart/form-data`，字段 `file`
- 响应：`{"ingredients": ["鸡蛋", "番茄", ...], "count": 5}`

### POST /api/recipe
选择路线获取菜谱。
- 请求：`{"ingredients": ["鸡蛋", "番茄"], "route": "香了"}`
- 香了响应：RAG 检索的真实菜谱 + 正常度分数
- 疯了响应：LLM 生成的创意菜谱 + 正常度分数 + `can_fallback: true`

### POST /api/fallback
疯了路线兜底，切换到 RAG。
- 请求：`{"ingredients": ["鸡蛋", "番茄"]}`
- 响应：同香了路线

### GET /health
健康检查。

## 小程序前端调用示例

```javascript
// 1. 上传照片识别食材
wx.uploadFile({
  url: 'https://your-domain.com/api/recognize',
  filePath: tempFilePath,
  name: 'file',
  success(res) {
    const data = JSON.parse(res.data)
    console.log(data.ingredients)
  }
})

// 2. 选路线获取菜谱
wx.request({
  url: 'https://your-domain.com/api/recipe',
  method: 'POST',
  data: {
    ingredients: ['鸡蛋', '番茄'],
    route: '疯了'
  },
  success(res) {
    console.log(res.data.recipe)
    console.log(res.data.normality)
  }
})

// 3. 兜底
wx.request({
  url: 'https://your-domain.com/api/fallback',
  method: 'POST',
  data: { ingredients: ['鸡蛋', '番茄'] },
  success(res) {
    console.log(res.data.recipes)
  }
})
```
