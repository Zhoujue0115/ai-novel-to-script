# AI 小说转剧本工具

将 3 个章节以上的小说文本自动转换为结构化 YAML 格式剧本初稿。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                     前端 (React + Vite)               │
│  ┌───────────┐  ┌───────────┐  ┌────────────────┐  │
│  │ NovelInput │  │YamlViewer │  │ ScriptPreview  │  │
│  │  标题+章节  │  │YAML+校验  │  │ 角色/场景/beats │  │
│  └─────┬─────┘  └───────────┘  └────────────────┘  │
│        │                                             │
│        ▼  POST /api/script/generate                  │
└────────┼────────────────────────────────────────────┘
         │  Vite Proxy → localhost:8000
         ▼
┌─────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ 输入校验  │  │ prompt   │  │ DeepSeek API     │  │
│  │ Pydantic │→│ builder  │→│ urllib (120s超时) │  │
│  └──────────┘  └──────────┘  └────────┬─────────┘  │
│                                       │              │
│                                       ▼              │
│                              ┌──────────────────┐   │
│                              │  yaml_validator   │   │
│                              │ YAML解析+字段检查  │   │
│                              └──────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```text
ai-novel-to-script/
├── docs/
│   ├── prd.md              # 产品需求文档
│   ├── schema.md            # YAML Schema 设计
│   └── tech-design.md       # 技术设计文档
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口 + CORS
│   │   ├── logger.py         # 统一日志
│   │   ├── api/script.py     # /generate + /validate 路由
│   │   ├── models/           # Pydantic 请求/响应模型
│   │   └── services/         # 生成器 + 校验器 + prompt
│   ├── tests/                # 单元测试 (pytest, 11 cases)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # 主页面 + 状态管理
│   │   ├── api.js            # Axios 后端调用
│   │   └── components/       # NovelInput / YamlViewer / ScriptPreview
│   ├── package.json
│   └── vite.config.js        # Vite + proxy 配置
├── prompts/
│   └── system_prompt.md      # 系统提示词文档
├── samples/
│   ├── sample_input.json     # 样例输入（3章小说）
│   └── sample_output.yaml    # 样例输出（完整YAML剧本）
└── README.md
```

## 开发状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | FastAPI 骨架 + /health + 校验 | ✅ |
| P1 | DeepSeek API + Prompt + YAML生成 | ✅ |
| P2 | 前端三栏 + 预览 + 导出 | ✅ |
| 增强 | 日志 + 异常处理 + 单元测试 + UI美化 | ✅ |

## 前置依赖

- Python 3.9+
- Node.js 18+
- DeepSeek API Key

## 快速启动

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # 编辑 .env 填入 LLM_API_KEY
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`

## 运行测试

```bash
cd backend
.venv\Scripts\activate
python -m pytest tests/ -v
```

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/api/script/generate` | 生成剧本（需 3 章以上） |
| POST | `/api/script/validate` | 校验 YAML 文本 |
| GET | `/docs` | Swagger 文档 |

### 请求示例

```json
POST /api/script/generate
{
  "title": "小说标题",
  "chapters": [
    {"index": 1, "title": "第一章", "content": "..."},
    {"index": 2, "title": "第二章", "content": "..."},
    {"index": 3, "title": "第三章", "content": "..."}
  ],
  "style": "screenplay"
}
```

详见 `samples/sample_input.json` 和 `samples/sample_output.yaml`。
