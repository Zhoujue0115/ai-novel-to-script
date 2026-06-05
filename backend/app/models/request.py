from pydantic import BaseModel, Field, field_validator


class ChapterInput(BaseModel):
    index: int = Field(ge=1, description="章节序号")
    title: str = Field(min_length=1, description="章节标题")
    content: str = Field(min_length=1, description="章节正文")


class GenerateScriptRequest(BaseModel):
    title: str = Field(min_length=1, description="小说标题")
    chapters: list[ChapterInput] = Field(min_length=3, description="章节列表，至少 3 个")
    style: str = Field(default="screenplay", description="剧本风格")

    @field_validator("chapters")
    @classmethod
    def check_min_chapters(cls, v: list[ChapterInput]) -> list[ChapterInput]:
        if len(v) < 3:
            raise ValueError("至少需要输入 3 个章节")
        return v


class ValidateScriptRequest(BaseModel):
    yaml_text: str = Field(min_length=1, description="待校验的 YAML 文本")
