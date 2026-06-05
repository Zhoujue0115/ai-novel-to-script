# Technical Design Document
# 技术设计文档

## 1. 技术栈

本项目采用前后端分离的轻量架构，重点突出后端接口设计、文本处理流程、结构化生成和 YAML 校验能力。

### 1.1 后端技术栈

| 技术 | 用途 |
|---|---|
| FastAPI | 构建后端 API 服务 |
| Pydantic | 请求参数和响应数据校验 |
| PyYAML | YAML 解析与生成 |
| Uvicorn | FastAPI 开发服务器 |
| python-dotenv | 管理环境变量 |
| 大模型 API | 小说理解与剧本生成 |

前后端分离架构下，FastAPI 需配置 CORS 中间件以允许前端跨域请求。

### 1.2 前端技术栈

| 技术 | 用途 |
|---|---|
| React / Vite | 构建单页应用 |
| Axios | 调用后端 API |
| js-yaml | 前端 YAML 解析和预览 |
| CSS / Tailwind CSS | 页面样式 |

### 1.3 文档与工程工具

| 工具 | 用途 |
|---|---|
| Markdown | 编写 PRD、Schema 和技术文档 |
| Git | 版本管理 |
| GitHub / Gitee | 代码仓库和 PR 管理 |

### 1.4 环境变量

后端通过 `.env` 文件管理敏感配置，不提交到 Git 仓库：

```bash
# .env
LLM_API_KEY=your-api-key
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

## 2. 系统架构

系统采用前后端分离架构。

用户
 │
 ▼
前端页面
 │
 │ 1. 输入小说标题和章节内容
 │ 2. 点击生成剧本
 ▼
后端 FastAPI 服务
 │
 ├─ 输入校验模块
 ├─ 章节解析模块
 ├─ AI 生成模块
 ├─ YAML 校验模块
 └─ 响应格式化模块
 │
 ▼
返回 YAML 剧本 + 结构化结果 + 校验状态
 │
 ▼
前端展示 YAML 和剧本预览
## 3. 模块划分
### 3.1 前端模块
NovelInput
负责小说输入。

功能：

输入小说标题
输入章节标题
输入章节正文
添加章节
提交生成请求
YamlViewer
负责展示生成的 YAML 文本。

功能：

显示 YAML 内容
支持复制
支持下载 .yaml
ScriptPreview
负责将结构化剧本渲染为可读视图。

功能：

展示角色列表
展示场景列表
展示对白、动作和旁白
GenerateButton
负责触发生成流程并展示加载状态。

功能：

请求后端 API
展示生成中状态
处理错误提示
### 3.2 后端模块
API 路由模块
负责定义 HTTP 接口。

主要接口：

POST /api/script/generate
POST /api/script/validate
GET /health
请求和响应模型模块
使用 Pydantic 定义请求和响应结构。

主要模型：

ChapterInput
GenerateScriptRequest
GenerateScriptResponse
ValidationResult
章节解析模块
负责处理输入章节。

功能：

校验章节数量是否不少于 3
清洗章节文本
生成章节摘要，或交给 AI 处理
AI 生成模块
负责调用大模型。

功能：

构建 Prompt
调用模型 API
获取 YAML 文本结果
处理模型异常
YAML 校验模块
负责检查生成结果。

功能：

检查 YAML 是否可解析
检查必要字段是否存在
检查 scenes 和 characters 是否为空
返回校验结果
## 4. API 设计
### 4.1 健康检查接口
请求
http
GET /health
响应

{
  "status": "ok"
}
### 4.2 生成剧本接口
请求
http
POST /api/script/generate
Request Body

{
  "title": "小说标题",
  "chapters": [
    {
      "index": 1,
      "title": "第一章",
      "content": "章节正文"
    },
    {
      "index": 2,
      "title": "第二章",
      "content": "章节正文"
    },
    {
      "index": 3,
      "title": "第三章",
      "content": "章节正文"
    }
  ],
  "style": "screenplay"
}
Response Body

{
  "success": true,
  "yaml_text": "title: ...",
  "structured_script": {},
  "validation": {
    "valid": true,
    "errors": []
  }
}
### 4.3 YAML 校验接口
请求
http
POST /api/script/validate
Request Body

{
  "yaml_text": "title: ..."
}
Response Body

{
  "valid": true,
  "errors": []
}
## 5. 生成流程
系统生成流程如下：


1. 用户输入小说标题和至少 3 个章节
2. 前端提交请求到后端
3. 后端校验输入数据
4. 后端构建 Prompt
5. 调用大模型生成 YAML 剧本
6. 使用 PyYAML 解析生成结果
7. 检查必要字段
8. 返回 YAML 文本、结构化结果和校验状态
9. 前端展示 YAML 和剧本预览
### 5.1 Prompt 生成策略
Prompt 需要明确约束模型输出：

必须输出 YAML。
不要输出 Markdown 代码块。
必须包含 title、source_chapters、characters、scenes。
scenes 中必须包含 beats。
beats 的 type 只能是 narration、dialogue、action、stage_direction。
对白类型必须包含 character 字段。
每个场景必须包含 chapter_refs。
### 5.2 后处理策略
由于大模型输出可能存在格式问题，后端需要进行基础后处理：

去除多余 Markdown 代码块标记。
尝试使用 PyYAML 解析。
检查顶层字段是否完整。
如果校验失败，返回错误信息。
后续可扩展自动修复功能。
## 6. 错误处理
### 6.1 输入错误
当用户输入章节不足 3 个时，返回：


{
  "success": false,
  "message": "至少需要输入 3 个章节"
}
### 6.2 模型调用错误
当大模型 API 调用失败时，返回：


{
  "success": false,
  "message": "AI 生成失败，请稍后重试"
}
### 6.3 模型调用超时

当大模型 API 调用超时时，返回：

```json
{
  "success": false,
  "message": "AI 生成超时，请稍后重试"
}
```

建议设置 API 调用超时时间为 120 秒。

### 6.4 YAML 格式错误
当生成内容无法解析为 YAML 时，返回：


{
  "valid": false,
  "errors": [
    "生成结果不是合法 YAML"
  ]
}
### 6.5 必要字段缺失
当 YAML 缺少必要字段时，返回：


{
  "valid": false,
  "errors": [
    "缺少 characters 字段",
    "缺少 scenes 字段"
  ]
}
## 8. 当前阶段实现优先级

### P0（第一阶段，必须完成）

- FastAPI 项目骨架搭建
- `/health` 健康检查接口
- `/api/script/generate` 占位接口
- 请求/响应 Pydantic 模型
- YAML 校验基础能力

### P1（第二阶段，核心能力）

- 大模型 API 接入
- Prompt 构建与调用
- YAML 剧本生成与后处理
- 前端输入页面与 YAML 展示

### P2（第三阶段，体验增强）

- 剧本预览渲染
- YAML 导出下载
- 局部场景重新生成
- 历史记录与多版本对比

## 9. 后续扩展方向
后续可以继续扩展：

支持局部场景重新生成。
支持选择剧本风格。
支持多版本对比。
支持历史记录保存。
支持角色关系图。
支持更严格的 JSON Schema / YAML Schema 校验。












