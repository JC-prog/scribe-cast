import json

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.api.deps import get_redis_conn
from app.schemas.jobs import BatchStatusResponse, JobStatusResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _job_to_response(job: Job) -> JobStatusResponse:
    status = job.get_status(refresh=False)
    result = job.result if status == "finished" else None
    error = job.meta.get("error")
    return JobStatusResponse(job_id=job.id, status=status, meta=dict(job.meta), result=result, error=error)


# Registered before /{job_id} so the literal "batch" segment isn't swallowed by the job_id path param.
@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(batch_id: str, redis_conn: Redis = Depends(get_redis_conn)) -> BatchStatusResponse:
    raw = redis_conn.get(f"batch:{batch_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Unknown batch: {batch_id}")

    job_ids = json.loads(raw)
    jobs = [_job_to_response(Job.fetch(job_id, connection=redis_conn)) for job_id in job_ids]
    return BatchStatusResponse(batch_id=batch_id, jobs=jobs)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, redis_conn: Redis = Depends(get_redis_conn)) -> JobStatusResponse:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}") from exc

    return _job_to_response(job)
