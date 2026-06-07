"""长篇小说批量处理 —— 滑动窗口 + 角色状态注入 + RAG 检索增强"""

import yaml
from ..logger import get_logger
from .script_generator import generate_script_yaml
from ..rag.vector_store import index_chapters, search_chapters

logger = get_logger(__name__)
BATCH_SIZE = 8   # 每批处理章节数
OVERLAP = 0      # 不重叠，避免章节重复处理
RAG_THRESHOLD = 20  # 超过此章节数启用 RAG 索引


def _extract_character_summary(yaml_text: str) -> str:
    """从已生成的 YAML 中提取角色摘要，注入下一批次"""
    try:
        data = yaml.safe_load(yaml_text)
        chars = data.get("characters", [])
        if not chars:
            return ""
        lines = ["已知角色（来自前序章节）："]
        for ch in chars:
            traits = "、".join(ch.get("traits", []))
            lines.append(f"- {ch['name']}({ch['role']}): {ch.get('description','')}，性格：{traits}")
        return "\n".join(lines)
    except Exception:
        return ""


def _extract_setting_summary(yaml_text: str) -> str:
    """提取场景/设定摘要"""
    try:
        data = yaml.safe_load(yaml_text)
        settings = data.get("settings", {})
        locs = settings.get("locations", [])
        if not locs:
            return ""
        lines = ["已知地点："]
        for loc in locs:
            lines.append(f"- {loc['name']}: {loc.get('description','')}")
        return "\n".join(lines)
    except Exception:
        return ""


def batch_generate(title: str, chapters: list, style: str = "screenplay", progress_queue=None) -> dict:
    """批量生成：滑动窗口 + 角色状态跨批次传递"""
    n = len(chapters)
    logger.info(f"批量生成开始: {n} 章, batch_size={BATCH_SIZE}, overlap={OVERLAP}")

    # RAG 索引（超长小说）
    use_rag = n > RAG_THRESHOLD
    if use_rag:
        logger.info(f"章节数 {n} > {RAG_THRESHOLD}，启用 RAG 全文索引")
        try:
            col_name = index_chapters(title, chapters)
            logger.info(f"RAG 索引完成: {col_name}")
        except Exception as e:
            logger.warning(f"RAG 索引失败，降级为无检索模式: {e}")
            use_rag = False

    all_yaml_parts = []
    char_context = ""
    setting_context = ""

    total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE

    start = 0
    batch_idx = 0
    while start < n:
        end = min(start + BATCH_SIZE, n)
        batch_chapters = chapters[start:end]
        batch_idx += 1
        if progress_queue:
            progress_queue.put(f'data: {{"step":"batch","msg":"批次 {batch_idx}/{total_batches}: 第 {start+1}-{end} 章","batch":{batch_idx},"total":{total_batches}}}\\n\\n')
        logger.info(f"批次 {batch_idx}: 第 {start+1}-{end} 章 (共 {len(batch_chapters)} 章)")

        # RAG 检索：为当前批次检索相关前文
        rag_context = ""
        if use_rag and batch_idx > 1:
            # 用前一批生成的角色上下文作为查询
            query = f"{title} {char_context}"
            passages = search_chapters(title, query, top_k=3)
            if passages:
                rag_context = "## 相关前文片段\n" + "\n".join(passages)
                logger.info(f"RAG 注入 {len(passages)} 条前文片段")

        result = generate_script_yaml(
            title=f"{title} (第{start+1}-{end}章)",
            chapters=batch_chapters,
            style=style,
            rag_context=rag_context,
        )

        if result["success"]:
            all_yaml_parts.append(result["yaml_text"])
            char_context = _extract_character_summary(result["yaml_text"])
            setting_context = _extract_setting_summary(result["yaml_text"])
            if char_context:
                logger.info(f"批次 {batch_idx} 角色摘要已提取，将注入下一批")
        else:
            logger.warning(f"批次 {batch_idx} 生成失败: {result['message']}")

        # 滑动窗口：start 前进 BATCH_SIZE - OVERLAP
        start += BATCH_SIZE - OVERLAP

    # 合并所有批次的 YAML
    merged = _merge_yaml_parts(title, all_yaml_parts, chapters, style)
    logger.info(f"批量生成完成: {batch_idx} 批次 → {len(all_yaml_parts)} 成功")
    return {"success": True, "yaml_text": merged, "message": f"共处理 {batch_idx} 批次"}


def _merge_yaml_parts(title: str, parts: list, all_chapters: list, style: str) -> str:
    """合并多个批次的 YAML 输出"""
    if len(parts) == 1:
        return parts[0]

    all_chars = {}
    all_scenes = []
    all_locations = {}
    source_summaries = []

    for part in parts:
        try:
            data = yaml.safe_load(part)
        except Exception:
            continue
        if not data:
            continue

        for ch in data.get("characters", []):
            cid = ch.get("id", ch.get("name", ""))
            if cid not in all_chars:
                all_chars[cid] = ch

        for loc in data.get("settings", {}).get("locations", []):
            lid = loc.get("id", loc.get("name", ""))
            if lid not in all_locations:
                all_locations[lid] = loc

        all_scenes.extend(data.get("scenes", []))
        if data.get("source_chapters"):
            source_summaries.extend(data["source_chapters"])

    # Re-index characters and scenes
    char_id_map = {}
    final_chars = []
    for i, (_, ch) in enumerate(all_chars.items(), 1):
        new_id = f"c{i}"
        char_id_map[ch.get("id", ch.get("name"))] = new_id
        ch["id"] = new_id
        if "relationships" in ch:
            for rel in ch["relationships"]:
                rel["target"] = char_id_map.get(rel.get("target", ""), rel.get("target", ""))
        final_chars.append(ch)

    final_scenes = []
    for i, scene in enumerate(all_scenes, 1):
        scene["scene_id"] = f"s{i}"
        if "characters_in_scene" in scene:
            scene["characters_in_scene"] = [
                char_id_map.get(c, c) for c in scene["characters_in_scene"]
            ]
        final_scenes.append(scene)

    # 收集所有分部的 adaptation_notes
    all_omitted = []
    all_suggestions = []
    genre = ""
    era = ""
    for part in parts:
        try:
            d = yaml.safe_load(part)
            if d:
                notes = d.get("adaptation_notes", {})
                all_omitted.extend(notes.get("omitted_plots", []))
                all_suggestions.extend(notes.get("suggestions", []))
                genre = genre or d.get("metadata", {}).get("genre", "")
                era = era or d.get("settings", {}).get("era", "")
        except Exception:
            pass

    merged = {
        "title": title,
        "metadata": {
            "schema_version": "1.0",
            "genre": genre or "未分类",
            "style": style,
            "language": "zh-CN",
            "generated_by": "AI Novel to Script (batch)",
        },
        "source_chapters": source_summaries or [
            {"index": ch["index"], "title": ch["title"], "summary": ""}
            for ch in all_chapters
        ],
        "characters": final_chars,
        "settings": {
            "era": era or "未指定",
            "locations": list(all_locations.values()),
        },
        "scenes": final_scenes,
        "adaptation_notes": {
            "omitted_plots": all_omitted[:5] or [],
            "merged_scenes": [f"跨批次合并，共 {len(parts)} 个批次"],
            "suggestions": all_suggestions[:5] or [],
        },
    }

    # 修复每个场景和 beat 的必填字段
    for scene in merged["scenes"]:
        scene.setdefault("chapter_refs", [1])
        scene.setdefault("location", "未指定")
        scene.setdefault("time", "")
        scene.setdefault("summary", "")
        scene.setdefault("characters_in_scene", [])
        for beat in scene.get("beats", []):
            bt = beat.get("type", "narration")
            if bt not in ("narration", "dialogue", "action", "inner_monologue", "stage_direction"):
                beat["type"] = "narration"
            if bt in ("dialogue", "action", "inner_monologue") and "character" not in beat:
                beat["character"] = scene["characters_in_scene"][0] if scene["characters_in_scene"] else "c1"

    return yaml.dump(merged, allow_unicode=True, sort_keys=False)
