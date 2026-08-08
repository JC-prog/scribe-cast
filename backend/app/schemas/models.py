from pydantic import BaseModel


class ModelInfo(BaseModel):
    size: str
    label: str
    hint: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class LanguageInfo(BaseModel):
    code: str
    label: str


class LanguagesResponse(BaseModel):
    languages: list[LanguageInfo]
