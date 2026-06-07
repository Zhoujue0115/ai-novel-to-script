"""长篇小说批量处理 —— 滑动窗口 + 角色状态注入 + RAG 检索增强"""

import yaml
from ..logger import get_logger
from .script_generator import generate_script_yaml
from ..rag.vector_store import index_chapters, search_chapters

logger = get_logger(__name__)
BATCH_SIZE = 8   # 每批处理章节数
OVERLAP = 2      # 窗口重叠章节数
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


def batch_generate(title: str, chapters: list, style: str = "screenplay") -> dict:
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

    start = 0
    batch_idx = 0
    while start < n:
        end = min(start + BATCH_SIZE, n)
        batch_chapters = chapters[start:end]
        batch_idx += 1
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

    merged = {
        "title": title,
        "metadata": {
            "schema_version": "1.0",
            "style": style,
            "language": "zh-CN",
            "generated_by": "AI Novel to Script (batch)",
        },
        "source_chapters": source_summaries or [
            {"index": ch["index"], "title": ch["title"]}
            for ch in all_chapters
        ],
        "characters": final_chars,
        "settings": {
            "locations": list(all_locations.values()),
        },
        "scenes": final_scenes,
        "adaptation_notes": {
            "merged_scenes": [f"跨批次合并，共 {len(parts)} 个批次"],
            "suggestions": [],
        },
    }

    return yaml.dump(merged, allow_unicode=True, sort_keys=False)
