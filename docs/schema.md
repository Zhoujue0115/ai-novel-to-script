# Database / API Schema
# YAML Schema 设计文档

## 1. 设计目标

本 YAML Schema 用于规范“AI 小说转剧本工具”的输出格式，使系统能够将 3 个章节以上的小说文本转换为结构化、可编辑、可校验的剧本初稿。

Schema 的主要目标包括：

1. 将小说中的人物、场景、对白、动作和旁白进行结构化组织。
2. 保留来源章节信息，方便作者追溯剧本内容来自哪一章。
3. 支持作者后续手动编辑和二次创作。
4. 使用 YAML 格式提升可读性，方便非技术用户理解。
5. 为后续扩展剧本预览、导出、校验和局部重生成提供统一数据结构。

## 2. 总体结构

YAML 顶层结构如下：

title: ""
metadata: {}
source_chapters: []
characters: []
settings: {}
scenes: []
adaptation_notes: {}

字段说明：

字段	类型	是否必填	说明
title	string	是	剧本标题
metadata	object	否	剧本元信息
source_chapters	array	是	来源小说章节
characters	array	是	角色列表
settings	object	否	世界观、时代、地点等设定
scenes	array	是	剧本场景列表
adaptation_notes	object	否	改编说明
## 3. 字段定义
### 3.1 title

title: "雨夜重逢"
类型：string
是否必填：是
说明：剧本标题，可以来自小说标题，也可以由 AI 根据内容生成。
设计原因：

剧本标题是作品的基本标识，便于导出、展示和后续管理。

### 3.2 metadata

metadata:
  genre: "都市情感"
  style: "screenplay"
  language: "zh-CN"
  generated_by: "AI Novel to Script"
类型：object
是否必填：否
说明：记录剧本的基础元信息。
字段：

字段	类型	说明
genre	string	题材类型
style	string	剧本类型，如 screenplay、stage_play
language	string	语言
generated_by	string	生成来源
设计原因：

metadata 用于记录剧本生成背景，便于后续扩展不同剧本类型和风格。

### 3.3 source_chapters

source_chapters:
  - index: 1
    title: "第一章 雨夜"
    summary: "女主在雨夜回到旧城，并意外遇见多年未见的男主。"
  - index: 2
    title: "第二章 旧事"
    summary: "两人回忆过去，矛盾逐渐浮现。"
类型：array
是否必填：是
说明：记录剧本改编所依据的小说章节。
每个章节对象包含：

字段	类型	是否必填	说明
index	integer	是	章节序号
title	string	是	章节标题
summary	string	否	章节摘要
设计原因：

剧本改编需要保留来源上下文。通过 source_chapters，作者可以知道剧本内容来自哪些小说章节，方便回查和修改。

### 3.4 characters

characters:
  - id: "c1"
    name: "林夏"
    role: "protagonist"
    description: "年轻小说作者，性格敏感但坚韧。"
    traits:
      - "敏感"
      - "坚韧"
    relationships:
      - target: "c2"
        relation: "旧识"
类型：array
是否必填：是
说明：角色列表，用于统一管理剧本中的人物。
角色字段：

字段	类型	是否必填	说明
id	string	是	角色唯一标识
name	string	是	角色名称
role	string	是	角色类型，如 protagonist、supporting、antagonist
description	string	否	角色简介
traits	array	否	性格特征
relationships	array	否	角色关系
设计原因：

小说中人物可能反复出现，如果不统一管理，生成剧本时容易出现称呼不一致的问题。通过角色表可以提升剧本结构的一致性。

### 3.5 settings

settings:
  era: "现代"
  locations:
    - id: "l1"
      name: "旧城咖啡馆"
      description: "位于老街尽头，灯光昏黄。"
类型：object
是否必填：否
说明：记录故事背景和主要地点。
字段：

字段	类型	说明
era	string	故事时代背景
locations	array	主要地点列表
设计原因：

剧本创作高度依赖场景。提前抽取地点信息，有助于后续分场和预览展示。

### 3.6 scenes

scenes:
  - scene_id: "s1"
    title: "雨夜重逢"
    chapter_refs:
      - 1
    location: "旧城咖啡馆"
    time: "夜晚"
    summary: "林夏在咖啡馆避雨时遇见多年未见的周言。"
    characters_in_scene:
      - "c1"
      - "c2"
    beats:
      - type: "narration"
        content: "雨水敲打着咖啡馆的玻璃窗，街灯在水雾中晕开。"
      - type: "action"
        character: "c1"
        content: "林夏推门而入，抖落伞上的雨水。"
      - type: "dialogue"
        character: "c2"
        content: "好久不见。"
      - type: "dialogue"
        character: "c1"
        content: "我没想到会在这里遇见你。"
类型：array
是否必填：是
说明：剧本主体内容，以场景为基本单位。
场景字段：

字段	类型	是否必填	说明
scene_id	string	是	场景唯一标识
title	string	是	场景标题
chapter_refs	array	是	对应的来源章节编号
location	string	是	场景地点
time	string	否	场景时间
summary	string	否	场景概要
characters_in_scene	array	是	当前场景出场角色 ID
beats	array	是	场景内容块
设计原因：

剧本通常以场景为基本结构。将内容拆成 scenes，可以让作者逐场修改，也方便后续进行局部重生成。

### 3.7 beats
beats 是每个场景中的最小内容块。


beats:
  - type: "dialogue"
    character: "c1"
    content: "你为什么回来？"
字段：

字段	类型	是否必填	说明
type	string	是	内容类型
character	string	条件必填	对白或动作对应角色
content	string	是	具体内容
type 可选值：

类型	说明
narration	旁白
dialogue	对白
action	动作
stage_direction	舞台或镜头提示
设计原因：

小说文本通常混合叙事、描写和对白。通过 beats 将其拆分为不同类型，便于作者按剧本创作习惯进行修改。

### 3.8 adaptation_notes

adaptation_notes:
  omitted_plots:
    - "省略了第二章中与主线无关的回忆片段。"
  merged_scenes:
    - "将第一章街道路段与咖啡馆段落合并为一个场景。"
  suggestions:
    - "可以进一步强化男女主之间的冲突。"
类型：object
是否必填：否
说明：记录 AI 在改编过程中的取舍说明和后续建议。
设计原因：

小说改编为剧本时通常需要删减、合并和重排。通过 adaptation_notes，用户可以理解 AI 为什么这样改编，也方便后续人工调整。

## 4. 示例 YAML

title: "雨夜重逢"
metadata:
  genre: "都市情感"
  style: "screenplay"
  language: "zh-CN"
  generated_by: "AI Novel to Script"

source_chapters:
  - index: 1
    title: "第一章 雨夜"
    summary: "林夏在雨夜回到旧城。"
  - index: 2
    title: "第二章 旧事"
    summary: "林夏回忆与周言的过去。"
  - index: 3
    title: "第三章 重逢"
    summary: "林夏与周言在咖啡馆重逢。"

characters:
  - id: "c1"
    name: "林夏"
    role: "protagonist"
    description: "年轻小说作者，外表冷静，内心敏感。"
    traits:
      - "敏感"
      - "坚韧"
    relationships:
      - target: "c2"
        relation: "旧识"
  - id: "c2"
    name: "周言"
    role: "supporting"
    description: "林夏多年未见的旧友。"
    traits:
      - "克制"
      - "沉稳"
    relationships:
      - target: "c1"
        relation: "旧识"

settings:
  era: "现代"
  locations:
    - id: "l1"
      name: "旧城咖啡馆"
      description: "老街尽头的咖啡馆，灯光昏黄。"

scenes:
  - scene_id: "s1"
    title: "雨夜重逢"
    chapter_refs:
      - 1
      - 3
    location: "旧城咖啡馆"
    time: "夜晚"
    summary: "林夏在雨夜进入咖啡馆避雨，意外遇见周言。"
    characters_in_scene:
      - "c1"
      - "c2"
    beats:
      - type: "narration"
        content: "雨水敲打着玻璃窗，咖啡馆里只有几盏昏黄的灯。"
      - type: "action"
        character: "c1"
        content: "林夏推门而入，收起湿透的雨伞。"
      - type: "dialogue"
        character: "c2"
        content: "好久不见。"
      - type: "dialogue"
        character: "c1"
        content: "我没想到会在这里遇见你。"

adaptation_notes:
  omitted_plots:
    - "省略了部分环境描写。"
  merged_scenes:
    - "将街道避雨情节与咖啡馆重逢情节合并。"
  suggestions:
    - "后续可增加两人之间的冲突对白。"
## 5. 设计原因
本 Schema 的设计遵循以下原则：

### 5.1 以场景为核心
剧本的基本单位是场景，而不是小说章节。因此，Schema 使用 scenes 作为主体结构，每个场景包含地点、时间、人物和内容块。

### 5.2 保留章节来源
小说改编过程中需要追溯原文，因此每个场景都通过 chapter_refs 字段记录来源章节。

### 5.3 统一角色管理
characters 字段用于集中管理角色信息，避免在不同场景中出现角色名称不一致的问题。

### 5.4 区分内容类型
beats 中的 type 字段用于区分 narration、dialogue、action 和 stage_direction，使输出更接近真实剧本结构。

### 5.5 便于后续编辑和扩展
YAML 结构可读性较强，适合作者直接编辑。同时该结构也可以被程序解析，用于后续实现剧本预览、格式校验、导出和局部重生成。