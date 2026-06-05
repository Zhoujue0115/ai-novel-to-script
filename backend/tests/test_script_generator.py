"""测试生成器模块（不调用真实 API）"""

import sys
sys.path.insert(0, "..")

from app.services.script_generator import _clean_yaml_output


def test_clean_no_markdown():
    assert _clean_yaml_output("title: test\nscenes: []") == "title: test\nscenes: []"


def test_clean_yaml_fence():
    raw = "```yaml\ntitle: test\nscenes: []\n```"
    assert _clean_yaml_output(raw) == "title: test\nscenes: []"


def test_clean_leading_trailing_whitespace():
    assert _clean_yaml_output("  \n  title: test  \n  ") == "title: test"


def test_generate_empty_title():
    from app.services.script_generator import generate_script_yaml
    result = generate_script_yaml("", [{"index": 1, "title": "c1", "content": "test"}])
    assert result["success"] is False
    assert "标题" in result["message"]


def test_generate_no_api_key():
    import app.services.script_generator as mod
    original = mod.LLM_API_KEY
    mod.LLM_API_KEY = ""
    try:
        result = mod.generate_script_yaml("test", [
            {"index": 1, "title": "c1", "content": "test"},
            {"index": 2, "title": "c2", "content": "test"},
            {"index": 3, "title": "c3", "content": "test"},
        ])
        assert result["success"] is False
        assert "LLM_API_KEY" in result["message"]
    finally:
        mod.LLM_API_KEY = original
