from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []


class GenerateScriptResponse(BaseModel):
    success: bool
    yaml_text: str = ""
    structured_script: dict = {}
    validation: ValidationResult = ValidationResult(valid=True, errors=[])
    message: str = ""
