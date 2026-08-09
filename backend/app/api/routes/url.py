from fastapi import APIRouter, Depends, HTTPException
from rq import Queue

from app.api.deps import get_queue
from app.core.languages import resolve_language
from app.core.model_catalog import is_valid_model_size
from app.logging_config import get_logger, log_event
from app.schemas.jobs import UploadResponse
from app.schemas.url import UrlTranscribeRequest
from app.worker.task_names import TASK_TRANSCRIBE_URL

router = APIRouter(prefix="/api/url", tags=["url"])
logger = get_logger("scribecast.api.url")


@router.post("/transcribe", response_model=UploadResponse)
def transcribe_url(request: UrlTranscribeRequest, queue: Queue = Depends(get_queue)) -> UploadResponse:
    if not is_valid_model_size(request.model_size):
        raise HTTPException(status_code=400, detail=f"Unknown model size: {request.model_size}")
    try:
        resolved_language = resolve_language(request.language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = queue.enqueue(TASK_TRANSCRIBE_URL, request.url, request.model_size, resolved_language)
    log_event(logger, "url_enqueued", job_id=job.id, url=request.url, model=request.model_size)
    return UploadResponse(job_id=job.id)
