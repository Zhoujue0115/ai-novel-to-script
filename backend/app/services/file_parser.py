"""TXT 文件解析 —— 自动编码检测 + 章节拆分"""

import re
import chardet
from ..logger import get_logger

logger = get_logger(__name__)

# 支持的编码列表（按优先级）
ENCODINGS = ["utf-8", "gbk", "gb2312", "gb18030", "utf-16", "utf-16le", "utf-16be", "big5"]


def detect_and_read(file_path: str) -> str:
    """检测文件编码并返回文本内容"""
    with open(file_path, "rb") as f:
        raw = f.read()

    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8") if result else "utf-8"
    confidence = result.get("confidence", 0) if result else 0
    logger.info(f"编码检测: {encoding} (置信度 {confidence:.0%})")

    # 尝试检测到的编码，失败则逐个尝试
    for enc in [encoding] + ENCODINGS:
        try:
            text = raw.decode(enc)
            logger.info(f"成功用 {enc} 解码，{len(text)} 字符")
            return text
        except (UnicodeDecodeError, LookupError):
            continue

    # 最终 fallback：忽略错误
    logger.warning("所有编码失败，用 utf-8 忽略错误")
    return raw.decode("utf-8", errors="replace")


def split_chapters(text: str) -> list[dict]:
    """从文本中拆分章节"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 多种章节标记匹配（统一处理"第X章""第 X 章""第一章"等格式）
    patterns = [
        (r"^[第序]\s*[一二三四五六七八九十百千0-9]+\s*[章回节卷集]\b", True),   # 第X章 / 第 3 章
        (r"^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+\d+\b", False),                     # Chapter 1
        (r"^[第序]\s*[一二三四五六七八九十百千0-9]+\s*[篇部]\b", True),          # 第X篇
        (r"^第\s*[0-9]+\s*章", True),                                            # 第1章（纯数字）
    ]

    best_matches = []
    for pattern, _ in patterns:
        matches = [(m.start(), m.group().strip()) for m in re.finditer(pattern, text, re.MULTILINE)]
        if len(matches) >= 3:
            best_matches = matches
            break

    if len(best_matches) < 3:
        # 回退：按连续空行拆分
        parts = [p.strip() for p in re.split(r"\n{3,}", text) if len(p.strip()) > 50]
        if len(parts) >= 3:
            return [{"index": i + 1, "title": f"第 {i+1} 章", "content": parts[i]} for i in range(len(parts))]
        # 整篇当一章
        return [{"index": 1, "title": "全文", "content": text}]

    chapters = []
    for i in range(len(best_matches)):
        start = best_matches[i][0]
        end = best_matches[i + 1][0] if i + 1 < len(best_matches) else len(text)
        header = best_matches[i][1]
        # 提取标题行（章节标记后面到换行符）
        line_end = text.find("\n", start)
        header_line = text[start:line_end].strip() if line_end != -1 else header
        body = text[line_end + 1:end].strip() if line_end != -1 else text[start + len(header):end].strip()
        title = header_line if len(header_line) > len(header) else header
        chapters.append({"index": i + 1, "title": title, "content": body})

    logger.info(f"拆分完成: {len(chapters)} 章")
    return chapters
