from typing import Any

from pydantic import BaseModel


class UploadResponse(BaseModel):
    job_id: str


class ValidateModelRequest(BaseModel):
    model_size: str


class ValidateModelResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    meta: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    enqueued_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class BatchStatusResponse(BaseModel):
    batch_id: str
    jobs: list[JobStatusResponse]


class JobListResponse(BaseModel):
    jobs: list[JobStatusResponse]
