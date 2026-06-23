"""YAML 剧本校验与自动修复模块"""

import yaml

REQUIRED_TOP_FIELDS = ["title", "source_chapters", "characters", "scenes"]
REQUIRED_SCENE_FIELDS = ["scene_id", "title", "chapter_refs", "location", "characters_in_scene", "beats"]
VALID_BEAT_TYPES = {"narration", "dialogue", "action", "inner_monologue", "stage_direction"}


def _auto_fix_beat(beat: dict, scene: dict):
    """自动修复 beat 的常见小问题"""
    bt = beat.get("type", "narration")
    # 修复无效 type
    if bt not in VALID_BEAT_TYPES:
        beat["type"] = "narration"
        bt = "narration"
    # 修复对白/动作/独白缺少 character
    if bt in ("dialogue", "action", "inner_monologue") and "character" not in beat:
        chars = scene.get("characters_in_scene", [])
        beat["character"] = chars[0] if chars else "c1"


def validate_yaml(yaml_text: str) -> dict:
    """校验 YAML，并尽量自动修复"""
    errors: list[str] = []

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return {"valid": False, "errors": ["生成结果不是合法 YAML"]}

    if not isinstance(data, dict):
        return {"valid": False, "errors": ["YAML 顶层必须是对象"]}

    # 补全顶层字段
    for field in REQUIRED_TOP_FIELDS:
        if field not in data or data[field] is None:
            if field == "source_chapters":
                data[field] = []
            elif field == "characters":
                data[field] = []
            elif field == "scenes":
                data[field] = []
            else:
                errors.append(f"缺少 {field} 字段")

    if "scenes" in data and isinstance(data["scenes"], list):
        for i, scene in enumerate(data["scenes"]):
            for field in REQUIRED_SCENE_FIELDS:
                if field not in scene or scene[field] is None:
                    if field == "chapter_refs":
                        scene[field] = [1]
                    elif field == "characters_in_scene":
                        scene[field] = []
                    elif field == "beats":
                        scene[field] = []
                    elif field == "scene_id":
                        scene[field] = f"s{i+1}"
                    else:
                        scene[field] = ""
            if "beats" in scene and isinstance(scene["beats"], list):
                for j, beat in enumerate(scene["beats"]):
                    if "type" not in beat:
                        beat["type"] = "narration"
                    _auto_fix_beat(beat, scene)

    fixed_text = yaml.dump(data, allow_unicode=True, sort_keys=False)
    return {"valid": len(errors) == 0, "errors": errors, "fixed_yaml": fixed_text}
