"""YAML 剧本校验模块"""

import yaml

REQUIRED_TOP_FIELDS = ["title", "source_chapters", "characters", "scenes"]
REQUIRED_SCENE_FIELDS = ["scene_id", "title", "chapter_refs", "location", "characters_in_scene", "beats"]
VALID_BEAT_TYPES = {"narration", "dialogue", "action", "inner_monologue", "stage_direction"}


def validate_yaml(yaml_text: str) -> dict:
    errors: list[str] = []

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return {"valid": False, "errors": ["生成结果不是合法 YAML"]}

    if not isinstance(data, dict):
        return {"valid": False, "errors": ["YAML 顶层必须是对象"]}

    for field in REQUIRED_TOP_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"缺少 {field} 字段")

    if "scenes" in data and isinstance(data["scenes"], list):
        for i, scene in enumerate(data["scenes"]):
            for field in REQUIRED_SCENE_FIELDS:
                if field not in scene or scene[field] is None:
                    errors.append(f"场景 [{i}] 缺少 {field} 字段")
            if "beats" in scene and isinstance(scene["beats"], list):
                for j, beat in enumerate(scene["beats"]):
                    if "type" not in beat:
                        errors.append(f"场景 [{i}] beat [{j}] 缺少 type 字段")
                    elif beat["type"] not in VALID_BEAT_TYPES:
                        errors.append(f"场景 [{i}] beat [{j}] type 值无效: {beat['type']}")
                    if beat.get("type") in ("dialogue", "action") and "character" not in beat:
                        errors.append(f"场景 [{i}] beat [{j}] ({beat['type']}) 缺少 character 字段")

    return {"valid": len(errors) == 0, "errors": errors}
