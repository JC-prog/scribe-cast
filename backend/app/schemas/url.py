from urllib.parse import urlparse

from pydantic import BaseModel, field_validator


class UrlTranscribeRequest(BaseModel):
    url: str
    model_size: str
    language: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("url must be a valid http(s) URL")
        return value
