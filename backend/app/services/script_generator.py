"""剧本生成服务 —— 调用 DeepSeek API"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv

from ..logger import get_logger
from .prompt_builder import build_user_prompt, SYSTEM_PROMPT

load_dotenv()
logger = get_logger(__name__)

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
TIMEOUT_SECONDS = 120


def _clean_yaml_output(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```ya?ml\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def generate_script_yaml(title: str, chapters: list, style: str = "screenplay", rag_context: str = "") -> dict:
    logger.info(f"开始生成剧本: title='{title}', chapters={len(chapters)}, style={style}")

    if not title.strip():
        logger.warning("标题为空")
        return {"success": False, "yaml_text": "", "message": "标题不能为空"}

    if not chapters:
        logger.warning("章节列表为空")
        return {"success": False, "yaml_text": "", "message": "章节列表为空"}

    if not LLM_API_KEY:
        logger.error("LLM_API_KEY 未配置")
        return {"success": False, "yaml_text": "", "message": "未配置 LLM_API_KEY，请检查 .env 文件"}

    user_prompt = build_user_prompt(title, chapters, style)
    if rag_context:
        user_prompt = f"{rag_context}\n\n---\n\n{user_prompt}"
        logger.info(f"Prompt 构建完成（含 RAG 上下文），长度: {len(user_prompt)} 字符")
    else:
        logger.info(f"Prompt 构建完成，长度: {len(user_prompt)} 字符")

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

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            elapsed = time.time() - start
            data = json.loads(resp.read().decode("utf-8"))
            logger.info(f"模型返回成功，耗时 {elapsed:.1f}s")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        logger.error(f"模型 API HTTP {e.code}，耗时 {elapsed:.1f}s")
        if e.code == 401:
            return {"success": False, "yaml_text": "", "message": "API Key 无效，请检查 LLM_API_KEY"}
        if e.code == 429:
            return {"success": False, "yaml_text": "", "message": "API 请求过于频繁，请稍后重试"}
        return {"success": False, "yaml_text": "", "message": f"模型 API 错误 ({e.code})"}
    except TimeoutError:
        elapsed = time.time() - start
        logger.error(f"模型调用超时，已等待 {elapsed:.1f}s")
        return {"success": False, "yaml_text": "", "message": "AI 生成超时，请稍后重试"}
    except Exception as e:
        logger.error(f"模型调用异常: {e}")
        return {"success": False, "yaml_text": "", "message": f"AI 生成失败: {str(e)}"}

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    if not content:
        logger.warning("模型返回内容为空")
        return {"success": False, "yaml_text": "", "message": "模型返回内容为空，请重试"}

    yaml_text = _clean_yaml_output(content)
    logger.info(f"YAML 清洗完成，长度: {len(yaml_text)} 字符")
    return {"success": True, "yaml_text": yaml_text, "message": ""}
