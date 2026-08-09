from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from rq import Queue

from app.api.deps import get_queue
from app.config import settings
from app.core.languages import resolve_language
from app.core.model_catalog import is_valid_model_size
from app.logging_config import get_logger, log_event
from app.schemas.jobs import UploadResponse
from app.utils.ids import new_id
from app.worker.task_names import TASK_TRANSCRIBE_UPLOAD

router = APIRouter(prefix="/api/upload", tags=["upload"])
logger = get_logger("scribecast.api.upload")

_CHUNK_SIZE = 1024 * 1024


@router.post("", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    model_size: str = Form(...),
    language: str = Form(...),
    translate: bool = Form(False),
    queue: Queue = Depends(get_queue),
) -> UploadResponse:
    if not is_valid_model_size(model_size):
        raise HTTPException(status_code=400, detail=f"Unknown model size: {model_size}")
    try:
        resolved_language = resolve_language(language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename).suffix
    upload_path = settings.uploads_dir / f"{new_id()}{suffix}"

    with upload_path.open("wb") as out_file:
        while chunk := await file.read(_CHUNK_SIZE):
            out_file.write(chunk)

    job = queue.enqueue(
        TASK_TRANSCRIBE_UPLOAD, str(upload_path), file.filename, model_size, resolved_language, translate
    )
    log_event(logger, "upload_enqueued", job_id=job.id, source_filename=file.filename, model=model_size)
    return UploadResponse(job_id=job.id)
