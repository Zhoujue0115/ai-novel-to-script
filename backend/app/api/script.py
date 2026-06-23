import os
import json
import queue
import threading
import tempfile
from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import StreamingResponse

from ..logger import get_logger
from ..models.request import GenerateScriptRequest, StatsRequest, ValidateScriptRequest
from ..models.response import GenerateScriptResponse, ValidationResult
from ..services.script_generator import generate_script_yaml
from ..services.batch_processor import batch_generate
import queue
import threading
import asyncio

from ..services.file_parser import detect_and_read, split_chapters
from ..chains.script_chain import generate_with_chain
from ..services.yaml_validator import validate_yaml
from ..services.stats_service import compute_stats

logger = get_logger(__name__)
router = APIRouter()

BATCH_THRESHOLD = 15
CHAIN_THRESHOLD = 6  # ≤6 章用 LangChain 多步链，7-15章基础生成，>15章批量


@router.post("/generate", response_model=GenerateScriptResponse)
def generate_script(req: GenerateScriptRequest):
    logger.info(f"收到生成请求: title='{req.title}', chapters={len(req.chapters)}")
    chapters_dicts = [ch.model_dump() for ch in req.chapters]

    if len(chapters_dicts) > BATCH_THRESHOLD:
        logger.info(f"章节数 {len(chapters_dicts)} 超过阈值，启用批量处理")
        result = batch_generate(req.title, chapters_dicts, req.style)
    elif len(chapters_dicts) <= CHAIN_THRESHOLD:
        logger.info(f"章节数 {len(chapters_dicts)}，使用 LangChain 多步链")
        try:
            result = generate_with_chain(req.title, chapters_dicts, req.style)
        except Exception as e:
            logger.error(f"LangChain 链异常，回退基础生成: {e}")
            result = generate_script_yaml(req.title, chapters_dicts, req.style)
    else:
        result = generate_script_yaml(req.title, chapters_dicts, req.style)

    if not result["success"]:
        logger.warning(f"生成失败: {result['message']}")
        return GenerateScriptResponse(
            success=False,
            yaml_text="",
            validation=ValidationResult(valid=False, errors=[]),
            message=result["message"],
        )

    logger.info("校验生成结果")
    validation = validate_yaml(result["yaml_text"])
    logger.info(f"校验结果: valid={validation['valid']}, errors={len(validation['errors'])}")
    return GenerateScriptResponse(
        success=True,
        yaml_text=validation.get("fixed_yaml", result["yaml_text"]),
        validation=ValidationResult(valid=validation["valid"], errors=validation["errors"]),
        message="",
    )


@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"收到文件上传: {file.filename}")
    # 保存临时文件
    suffix = os.path.splitext(file.filename or ".txt")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = detect_and_read(tmp_path)
        chapters = split_chapters(text)
        title = os.path.splitext(file.filename)[0] if file.filename else "未命名"
        return {
            "title": title,
            "chapter_count": len(chapters),
            "chapters": chapters,
        }
    finally:
        os.unlink(tmp_path)


@router.post("/generate/stream")
async def generate_stream(req: GenerateScriptRequest):
    """SSE 流式生成，推送进度事件"""
    q: queue.Queue = queue.Queue()

    def run():
        chapters_dicts = [ch.model_dump() for ch in req.chapters]
        n = len(chapters_dicts)
        if n > BATCH_THRESHOLD:
            totalBatches = (n + 7) // 8
            q.put(f'data: {{"step":"batch","msg":"批次 0/{totalBatches}: 准备中","batch":0,"total":{totalBatches}}}\n\n')
            result = batch_generate(req.title, chapters_dicts, req.style, progress_queue=q)
        elif n <= CHAIN_THRESHOLD:
            q.put("data: {\"step\":\"analyze\",\"msg\":\"正在分析角色与场景...\"}\n\n")
            try:
                result = generate_with_chain(req.title, chapters_dicts, req.style)
                q.put("data: {\"step\":\"generate\",\"msg\":\"正在生成剧本...\"}\n\n")
            except Exception as e:
                logger.error(f"链异常,回退: {e}")
                result = generate_script_yaml(req.title, chapters_dicts, req.style)
        else:
            q.put("data: {\"step\":\"generate\",\"msg\":\"正在生成剧本...\"}\n\n")
            result = generate_script_yaml(req.title, chapters_dicts, req.style)

        if result["success"]:
            q.put("data: {\"step\":\"validate\",\"msg\":\"正在校验结果...\"}\n\n")
            validation = validate_yaml(result["yaml_text"])
            result["yaml_text"] = validation.get("fixed_yaml", result["yaml_text"])
            stats = compute_stats(result["yaml_text"])
            payload = json.dumps({
                "yaml_text": result["yaml_text"],
                "validation": validation,
                "stats": stats,
            }, ensure_ascii=False)
            q.put(f"event: done\ndata: {payload}\n\n")
        else:
            q.put(f"data: {{\"step\":\"error\",\"msg\":\"{result['message']}\"}}\n\n")

    threading.Thread(target=run, daemon=True).start()

    async def event_gen():
        while True:
            try:
                msg = q.get_nowait()
                yield msg
                if msg.startswith("event: done") or '"step":"error"' in msg:
                    break
            except queue.Empty:
                yield ": heartbeat\n\n"
            await asyncio.sleep(0.3)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/stats", response_model=dict)
async def get_stats(req: StatsRequest):
    """计算剧本统计指标"""
    return compute_stats(req.yaml_text)


@router.post("/validate", response_model=ValidationResult)
def validate_script(req: ValidateScriptRequest):
    logger.info(f"收到校验请求，YAML 长度: {len(req.yaml_text)}")
    result = validate_yaml(req.yaml_text)
    logger.info(f"校验完成: valid={result['valid']}")
    return result
