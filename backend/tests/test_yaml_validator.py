"""测试 YAML 校验模块"""

import sys
sys.path.insert(0, "..")

from app.services.yaml_validator import validate_yaml

VALID_YAML = """title: "测试剧本"
source_chapters:
  - index: 1
    title: "第一章"
    summary: "测试"
characters:
  - id: "c1"
    name: "测试角色"
    role: "protagonist"
scenes:
  - scene_id: "s1"
    title: "测试场景"
    chapter_refs: [1]
    location: "测试地点"
    characters_in_scene: ["c1"]
    beats:
      - type: "narration"
        content: "旁白内容"
      - type: "dialogue"
        character: "c1"
        content: "对白内容"
      - type: "action"
        character: "c1"
        content: "动作内容"
"""


def test_valid_yaml():
    result = validate_yaml(VALID_YAML)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_not_yaml():
    # yaml.safe_load returns None for empty string, not YAMLError
    result = validate_yaml("")
    assert result["valid"] is False
    assert len(result["errors"]) >= 1


def test_missing_top_fields():
    result = validate_yaml("title: test")
    # 缺少的字段会被自动补全
    assert result["valid"] is True


def test_missing_scene_field():
    result = validate_yaml("""title: "test"
source_chapters:
  - index: 1
    title: "ch1"
characters: []
scenes:
  - scene_id: "s1"
    title: "scene"
    chapter_refs: [1]
    location: "loc"
    characters_in_scene: []
    beats: []
""")
    assert result["valid"] is True


def test_invalid_beat_type():
    result = validate_yaml("""title: "test"
source_chapters:
  - index: 1
    title: "ch1"
characters: []
scenes:
  - scene_id: "s1"
    title: "scene"
    chapter_refs: [1]
    location: "loc"
    characters_in_scene: []
    beats:
      - type: "singing"
        content: "唱了一段歌"
""")
    assert result["valid"] is True  # beat type auto-fixed to narration


def test_dialogue_missing_character():
    result = validate_yaml("""title: "test"
source_chapters:
  - index: 1
    title: "ch1"
characters: []
scenes:
  - scene_id: "s1"
    title: "scene"
    chapter_refs: [1]
    location: "loc"
    characters_in_scene: []
    beats:
      - type: "dialogue"
        content: "缺少角色字段的对白"
""")
    assert result["valid"] is True  # character auto-filled from scene
