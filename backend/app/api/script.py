from fastapi import APIRouter

from ..logger import get_logger
from ..models.request import GenerateScriptRequest, ValidateScriptRequest
from ..models.response import GenerateScriptResponse, ValidationResult
from ..services.script_generator import generate_script_yaml
from ..services.batch_processor import batch_generate
from ..chains.script_chain import generate_with_chain
from ..services.yaml_validator import validate_yaml

logger = get_logger(__name__)
router = APIRouter()

BATCH_THRESHOLD = 12
CHAIN_THRESHOLD = 6  # ≤6 章用 LangChain 多步链（更高质量），>6 ≤12 用基础生成


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
        yaml_text=result["yaml_text"],
        validation=ValidationResult(**validation),
        message="",
    )


@router.post("/validate", response_model=ValidationResult)
def validate_script(req: ValidateScriptRequest):
    logger.info(f"收到校验请求，YAML 长度: {len(req.yaml_text)}")
    result = validate_yaml(req.yaml_text)
    logger.info(f"校验完成: valid={result['valid']}")
    return result
