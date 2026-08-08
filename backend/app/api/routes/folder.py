import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from rq import Queue

from app.api.deps import get_queue, get_redis_conn
from app.config import settings
from app.core.folder_scanner import resolve_selected_videos, scan_folder
from app.core.languages import resolve_language
from app.core.model_catalog import is_valid_model_size
from app.core.paths import derive_output_path
from app.logging_config import get_logger, log_event
from app.schemas.folder import (
    DiscoveredVideoResponse,
    FolderScanRequest,
    FolderScanResponse,
    FolderTranscribeRequest,
    FolderTranscribeResponse,
)
from app.utils.ids import new_id
from app.worker.task_names import TASK_TRANSCRIBE_FOLDER_ITEM

router = APIRouter(prefix="/api/folder", tags=["folder"])
logger = get_logger("scribecast.api.folder")


@router.post("/scan", response_model=FolderScanResponse)
def scan(request: FolderScanRequest) -> FolderScanResponse:
    videos = scan_folder(Path(request.folder_path))
    return FolderScanResponse(
        videos=[
            DiscoveredVideoResponse(
                absolute_path=str(video.absolute_path),
                relative_path=str(video.relative_path),
                size_bytes=video.size_bytes,
                existing_srt=video.existing_srt,
            )
            for video in videos
        ]
    )


@router.post("/transcribe", response_model=FolderTranscribeResponse)
def transcribe(
    request: FolderTranscribeRequest,
    queue: Queue = Depends(get_queue),
    redis_conn: Redis = Depends(get_redis_conn),
) -> FolderTranscribeResponse:
    if not is_valid_model_size(request.model_size):
        raise HTTPException(status_code=400, detail=f"Unknown model size: {request.model_size}")
    try:
        resolved_language = resolve_language(request.language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    videos = resolve_selected_videos(Path(request.folder_path), request.video_paths)

    batch_id = new_id()
    job_ids = []
    for video_path in videos:
        output_path = derive_output_path(video_path)
        job = queue.enqueue(
            TASK_TRANSCRIBE_FOLDER_ITEM,
            str(video_path),
            str(output_path),
            request.model_size,
            resolved_language,
            batch_id,
        )
        job_ids.append(job.id)

    redis_conn.set(f"batch:{batch_id}", json.dumps(job_ids), ex=settings.batch_ttl_seconds)
    log_event(logger, "folder_batch_enqueued", batch_id=batch_id, video_count=len(job_ids), model=request.model_size)
    return FolderTranscribeResponse(batch_id=batch_id, job_ids=job_ids)
