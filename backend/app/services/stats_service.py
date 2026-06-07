"""剧本统计分析 —— 场景数/对白占比/角色台词量"""

import yaml
from collections import Counter


def compute_stats(yaml_text: str) -> dict:
    """从 YAML 计算剧本统计指标"""
    try:
        data = yaml.safe_load(yaml_text)
    except Exception:
        return {"error": "YAML 解析失败"}

    if not data or not isinstance(data, dict):
        return {"error": "剧本数据为空"}

    scenes = data.get("scenes", [])
    characters = data.get("characters", [])

    # 图表数据
    total_beats = 0
    beat_type_counts = Counter()
    char_line_counts = Counter()
    scene_char_counts = Counter()

    for scene in scenes:
        for beat in scene.get("beats", []):
            total_beats += 1
            beat_type_counts[beat.get("type", "unknown")] += 1
            if beat.get("character"):
                char_line_counts[beat["character"]] += 1
        for cid in scene.get("characters_in_scene", []):
            scene_char_counts[cid] += 1

    # 角色 ID → 名称映射
    char_map = {ch.get("id", ""): ch.get("name", ch.get("id", "")) for ch in characters}
    char_roles = {ch.get("id", ""): ch.get("role", "unknown") for ch in characters}

    # 类型标签
    TYPE_LABELS = {
        "narration": "旁白", "dialogue": "对白", "action": "动作",
        "inner_monologue": "独白", "stage_direction": "提示",
    }

    return {
        "total_scenes": len(scenes),
        "total_beats": total_beats,
        "total_characters": len(characters),
        "beat_distribution": [
            {"name": TYPE_LABELS.get(t, t), "value": c, "type": t}
            for t, c in sorted(beat_type_counts.items(), key=lambda x: -x[1])
        ],
        "character_lines": [
            {"name": char_map.get(cid, cid), "count": count, "role": char_roles.get(cid, "")}
            for cid, count in sorted(char_line_counts.items(), key=lambda x: -x[1])
        ],
        "character_scenes": [
            {"name": char_map.get(cid, cid), "count": count}
            for cid, count in sorted(scene_char_counts.items(), key=lambda x: -x[1])
        ],
        "dialogue_ratio": round(
            beat_type_counts.get("dialogue", 0) / max(total_beats, 1) * 100, 1
        ),
        "avg_beats_per_scene": round(total_beats / max(len(scenes), 1), 1),
    }
