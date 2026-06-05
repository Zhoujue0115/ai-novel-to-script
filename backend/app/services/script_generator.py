"""剧本生成服务 —— 调用 DeepSeek API"""

import json
import os
import re
import urllib.request
import urllib.error
from dotenv import load_dotenv

from .prompt_builder import build_user_prompt, SYSTEM_PROMPT

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
TIMEOUT_SECONDS = 120


def _clean_yaml_output(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```ya?ml\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def generate_script_yaml(title: str, chapters: list, style: str = "screenplay") -> dict:
    if not LLM_API_KEY:
        return {"success": False, "yaml_text": "", "message": "未配置 LLM_API_KEY"}

    user_prompt = build_user_prompt(title, chapters, style)

    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 8192,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{LLM_API_BASE}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"success": False, "yaml_text": "", "message": f"模型 API 错误: {e.code}"}
    except TimeoutError:
        return {"success": False, "yaml_text": "", "message": "AI 生成超时，请稍后重试"}
    except Exception as e:
        return {"success": False, "yaml_text": "", "message": f"AI 生成失败: {str(e)}"}

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    if not content:
        return {"success": False, "yaml_text": "", "message": "模型返回内容为空"}

    yaml_text = _clean_yaml_output(content)
    return {"success": True, "yaml_text": yaml_text, "message": ""}
