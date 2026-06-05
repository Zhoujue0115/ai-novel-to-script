# AI Novel to Script
# AI 小说转剧本工具

## 项目简介

本项目是一个 AI 辅助剧本创作工具，支持将 3 个章节以上的小说文本自动转换为结构化 YAML 格式剧本初稿，帮助小说作者快速获得可编辑、可进一步打磨的剧本结构。

## 选题方向

题目三：AI 小说转剧本工具

## 核心功能

- 小说章节输入
- AI 剧本生成
- YAML 格式输出
- 剧本预览
- YAML 导出
- YAML Schema 设计说明
- 基础结果校验

## 技术栈

后端：

- FastAPI
- Pydantic
- PyYAML

前端：

- React / Vite
- Axios
- js-yaml

## 项目结构

```text
ai-novel-to-script/
├── docs/
│   ├── prd.md
│   ├── schema.md
│   └── tech-design.md
├── backend/
├── frontend/
├── prompts/
├── samples/
└── README.md

