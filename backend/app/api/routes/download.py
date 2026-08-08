from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from redis import Redis
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.api.deps import get_redis_conn

router = APIRouter(prefix="/api/download", tags=["download"])


@router.get("/{job_id}")
def download_subtitle(job_id: str, redis_conn: Redis = Depends(get_redis_conn)) -> FileResponse:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}") from exc

    if job.get_status(refresh=False) != "finished":
        raise HTTPException(status_code=404, detail=f"Job not finished: {job_id}")

    output_path = job.meta.get("output_path")
    if not output_path or not Path(output_path).is_file():
        raise HTTPException(status_code=404, detail=f"Subtitle file not found for job: {job_id}")

    return FileResponse(output_path, media_type="text/plain", filename=Path(output_path).name)
