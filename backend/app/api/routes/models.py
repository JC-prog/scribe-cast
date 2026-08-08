from fastapi import APIRouter, Depends, HTTPException
from rq import Queue

from app.api.deps import get_queue
from app.core.model_catalog import is_valid_model_size, list_models
from app.schemas.jobs import ValidateModelRequest, ValidateModelResponse
from app.schemas.models import ModelsResponse
from app.worker.task_names import TASK_VALIDATE_MODEL

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelsResponse)
def get_models() -> ModelsResponse:
    return ModelsResponse(models=list_models())


@router.post("/validate", response_model=ValidateModelResponse)
def validate_model(request: ValidateModelRequest, queue: Queue = Depends(get_queue)) -> ValidateModelResponse:
    if not is_valid_model_size(request.model_size):
        raise HTTPException(status_code=400, detail=f"Unknown model size: {request.model_size}")
    job = queue.enqueue(TASK_VALIDATE_MODEL, request.model_size)
    return ValidateModelResponse(job_id=job.id)
