from fastapi import APIRouter

from ..models.request import GenerateScriptRequest
from ..models.response import GenerateScriptResponse, ValidationResult
from ..services.yaml_validator import validate_yaml

router = APIRouter()


@router.post("/generate", response_model=GenerateScriptResponse)
def generate_script(req: GenerateScriptRequest):
    return GenerateScriptResponse(
        success=True,
        yaml_text="",
        structured_script={},
        validation=ValidationResult(valid=True, errors=[]),
        message="生成接口已就绪，等待接入大模型",
    )


@router.post("/validate", response_model=ValidationResult)
def validate_script(yaml_text: str):
    return validate_yaml(yaml_text)
