"""LangChain 剧本生成链 —— 多步分析 + 生成 + 自查"""

from langchain_deepseek import ChatDeepSeek
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import os
from dotenv import load_dotenv

load_dotenv()

# ── Model ───────────────────────────────────────────
llm = ChatDeepSeek(
    model=os.getenv("LLM_MODEL", "deepseek-chat"),
    api_key=os.getenv("LLM_API_KEY", ""),
    api_base=os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1"),
    temperature=0.7,
    max_tokens=8192,
    timeout=120,
)

# ── Step 1: 角色与场景分析 ──────────────────────────
ANALYSIS_SYSTEM = """你是一个专业的小说分析员。仔细阅读小说章节，输出以下分析。用纯文本，不用 markdown。

## 输出格式

【角色分析】
每个角色一行：ID | 姓名 | 类型(protagonist/supporting/antagonist) | 简介 | 性格标签(逗号分隔)
角色关系行：ID1 -> ID2: 关系描述

【场景分析】
每个场景一行：场景编号 | 场景标题 | 所属章节 | 地点 | 时间 | 出场角色ID

【改编建议】
用 3 条以内的简短建议说明改编要点
"""

ANALYSIS_HUMAN = """## 小说信息
标题：{title}
风格：{style}

## 小说正文
{chapters_text}"""

analysis_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(ANALYSIS_SYSTEM),
    HumanMessagePromptTemplate.from_template(ANALYSIS_HUMAN),
])
analysis_chain = analysis_prompt | llm | StrOutputParser()


# ── Step 2: YAML 剧本生成 ────────────────────────────
SCRIPT_SYSTEM = """你是一个专业的小说改编剧本 AI。根据分析结果和原文，生成结构化 YAML 剧本。

你必须输出纯 YAML，不要用 Markdown 代码块包裹。

YAML 结构：
```yaml
title: "剧本标题"
metadata:
  schema_version: "1.0"
  genre: "题材"
  style: "{style}"
  language: "zh-CN"
  generated_by: "AI Novel to Script (LangChain)"
source_chapters:
  - index: 1
    title: "章节标题"
    summary: "摘要"
characters:
  - id: "c1"
    name: "角色名"
    role: "protagonist"
    description: "简介"
    traits: ["标签1"]
    relationships:
      - target: "c2"
        relation: "关系"
settings:
  era: "时代"
  locations:
    - id: "l1"
      name: "地点"
      description: "描述"
scenes:
  - scene_id: "s1"
    title: "场景标题"
    chapter_refs: [1]
    location: "地点"
    time: "时间"
    summary: "概要"
    characters_in_scene: ["c1"]
    beats:
      - type: "narration"       # narration/dialogue/action/inner_monologue/stage_direction
        content: "内容"
      - type: "dialogue"
        character: "c1"
        content: "对白"
adaptation_notes:
  omitted_plots: []
  merged_scenes: []
  suggestions: []
```

改编规则：
1. 根据分析结果中的角色信息填写 characters
2. 根据分析结果中的场景信息拆分 scenes
3. 每个 scene 的 beats 细粒度为 1-3 句一个 beat
4. dialogue/action/inner_monologue 必须包含 character 字段
5. 保留原文关键对白，不凭空编造
6. 每个 scene 通过 chapter_refs 标注来源
"""

SCRIPT_HUMAN = """## 小说原文
{chapters_text}

## 分析结果
{analysis}"""

script_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SCRIPT_SYSTEM),
    HumanMessagePromptTemplate.from_template(SCRIPT_HUMAN),
])
script_chain = script_prompt | llm | StrOutputParser()


# ── Step 3: 自检修正 ─────────────────────────────────
REVIEW_SYSTEM = """你是一个严格的 YAML 校验员。检查以下剧本 YAML，指出并修复问题。

常见问题：
- beats 的 type 不在 [narration, dialogue, action, inner_monologue, stage_direction] 中
- dialogue/action 缺少 character 字段
- source_chapters 缺少 index
- scenes 缺少 chapter_refs
- YAML 中有未闭合的引号

输出修正后的完整 YAML，不输出任何说明。"""

REVIEW_HUMAN = """## 待检查 YAML
{yaml_text}

## 参考原文
{chapters_text}"""

review_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(REVIEW_SYSTEM),
    HumanMessagePromptTemplate.from_template(REVIEW_HUMAN),
])
review_chain = review_prompt | llm | StrOutputParser()


# ── 完整生成链 ───────────────────────────────────────
def build_chapters_text(chapters: list) -> str:
    parts = []
    for ch in chapters:
        parts.append(f"## 第{ch['index']}章 {ch['title']}\n\n{ch['content']}")
    return "\n\n".join(parts)


def generate_with_chain(title: str, chapters: list, style: str = "screenplay") -> dict:
    """三阶段生成：分析 → 生成 → 自检"""
    chapters_text = build_chapters_text(chapters)

    # Step 1: 分析
    analysis_result = analysis_chain.invoke({
        "title": title,
        "style": style,
        "chapters_text": chapters_text,
    })

    # Step 2: 生成
    yaml_text = script_chain.invoke({
        "title": title,
        "style": style,
        "chapters_text": chapters_text,
        "analysis": analysis_result,
    })

    # 清洗 markdown 代码块
    yaml_text = yaml_text.strip()
    if yaml_text.startswith("```"):
        lines = yaml_text.split("\n")
        yaml_text = "\n".join(lines[1:])
        if yaml_text.endswith("```"):
            yaml_text = yaml_text[:-3].strip()

    # Step 3: 自检（可选，仅在格式有问题时）
    if len(yaml_text) < 200 or "scenes:" not in yaml_text:
        # 格式严重异常，重新生成
        yaml_text = review_chain.invoke({
            "yaml_text": yaml_text if len(yaml_text) > 0 else "(empty)",
            "chapters_text": chapters_text,
        })
        yaml_text = yaml_text.strip()
        if yaml_text.startswith("```"):
            lines = yaml_text.split("\n")
            yaml_text = "\n".join(lines[1:])
            if yaml_text.endswith("```"):
                yaml_text = yaml_text[:-3].strip()

    return {"success": True, "yaml_text": yaml_text, "message": ""}
