from fastapi import APIRouter

from ..models.request import GenerateScriptRequest, ValidateScriptRequest
from ..models.response import GenerateScriptResponse, ValidationResult
from ..services.script_generator import generate_script_yaml
from ..services.yaml_validator import validate_yaml

router = APIRouter()


@router.post("/generate", response_model=GenerateScriptResponse)
def generate_script(req: GenerateScriptRequest):
    chapters_dicts = [ch.model_dump() for ch in req.chapters]
    result = generate_script_yaml(req.title, chapters_dicts, req.style)

    if not result["success"]:
        return GenerateScriptResponse(
            success=False,
            yaml_text="",
            structured_script={},
            validation=ValidationResult(valid=False, errors=[]),
            message=result["message"],
        )

    validation = validate_yaml(result["yaml_text"])
    return GenerateScriptResponse(
        success=True,
        yaml_text=result["yaml_text"],
        structured_script={},
        validation=ValidationResult(**validation),
        message="",
    )


@router.post("/validate", response_model=ValidationResult)
def validate_script(req: ValidateScriptRequest):
    return validate_yaml(req.yaml_text)
