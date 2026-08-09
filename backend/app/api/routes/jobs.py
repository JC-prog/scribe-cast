import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.api.deps import get_queue, get_redis_conn
from app.schemas.jobs import BatchStatusResponse, JobListResponse, JobStatusResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# RQ's job timestamps are naive UTC datetimes (no tzinfo) - match that here
# rather than attaching a timezone, so sort comparisons don't blow up.
_EPOCH = datetime.min


def _job_to_response(job: Job) -> JobStatusResponse:
    status = job.get_status(refresh=False)
    result = job.result if status == "finished" else None
    error = job.meta.get("error")
    return JobStatusResponse(
        job_id=job.id,
        status=status,
        meta=dict(job.meta),
        result=result,
        error=error,
        enqueued_at=job.enqueued_at.isoformat() if job.enqueued_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        ended_at=job.ended_at.isoformat() if job.ended_at else None,
    )


# Registered before /{job_id} so the literal "batch" segment isn't swallowed by the job_id path param.
@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(batch_id: str, redis_conn: Redis = Depends(get_redis_conn)) -> BatchStatusResponse:
    raw = redis_conn.get(f"batch:{batch_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Unknown batch: {batch_id}")

    job_ids = json.loads(raw)
    jobs = [_job_to_response(Job.fetch(job_id, connection=redis_conn)) for job_id in job_ids]
    return BatchStatusResponse(batch_id=batch_id, jobs=jobs)


@router.get("", response_model=JobListResponse)
def list_jobs(
    limit: int = 50,
    queue: Queue = Depends(get_queue),
    redis_conn: Redis = Depends(get_redis_conn),
) -> JobListResponse:
    limit = max(1, min(limit, 200))

    job_ids: set[str] = set(queue.job_ids)
    job_ids |= set(queue.started_job_registry.get_job_ids())
    job_ids |= set(queue.finished_job_registry.get_job_ids())
    job_ids |= set(queue.failed_job_registry.get_job_ids())

    jobs = [job for job in Job.fetch_many(job_ids, connection=redis_conn) if job is not None]
    jobs.sort(key=lambda job: job.enqueued_at or _EPOCH, reverse=True)

    return JobListResponse(jobs=[_job_to_response(job) for job in jobs[:limit]])


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, redis_conn: Redis = Depends(get_redis_conn)) -> JobStatusResponse:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}") from exc

    return _job_to_response(job)
