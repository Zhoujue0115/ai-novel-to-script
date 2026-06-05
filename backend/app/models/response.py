from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []


class GenerateScriptResponse(BaseModel):
    success: bool
    yaml_text: str = ""
    validation: ValidationResult = ValidationResult(valid=True, errors=[])
    message: str = ""
