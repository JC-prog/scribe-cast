import json

from rq.job import Job, JobStatus

from app.worker.task_names import TASK_VALIDATE_MODEL


def test_get_job_status_not_found(client):
    response = client.get("/api/jobs/does-not-exist")
    assert response.status_code == 404


def test_get_job_status_returns_queued_job(client, fake_queue):
    job = fake_queue.enqueue(TASK_VALIDATE_MODEL, "tiny")

    response = client.get(f"/api/jobs/{job.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job.id
    assert body["status"] == "queued"
    assert body["result"] is None


def test_get_batch_status_not_found(client):
    response = client.get("/api/jobs/batch/does-not-exist")
    assert response.status_code == 404


def test_get_batch_status_returns_all_jobs(client, fake_queue, fake_redis_conn):
    job_a = fake_queue.enqueue(TASK_VALIDATE_MODEL, "tiny")
    job_b = fake_queue.enqueue(TASK_VALIDATE_MODEL, "base")
    fake_redis_conn.set("batch:batch-1", json.dumps([job_a.id, job_b.id]))

    response = client.get("/api/jobs/batch/batch-1")

    assert response.status_code == 200
    body = response.json()
    assert body["batch_id"] == "batch-1"
    assert {j["job_id"] for j in body["jobs"]} == {job_a.id, job_b.id}


def test_get_job_status_reflects_failed_job_with_error_meta(client, fake_redis_conn):
    job = Job.create(func=TASK_VALIDATE_MODEL, args=("tiny",), connection=fake_redis_conn, meta={"error": "boom"})
    job.save()
    job.set_status(JobStatus.FAILED)

    response = client.get(f"/api/jobs/{job.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error"] == "boom"


def test_get_job_status_includes_timestamps(client, fake_queue):
    job = fake_queue.enqueue(TASK_VALIDATE_MODEL, "tiny")

    response = client.get(f"/api/jobs/{job.id}")

    body = response.json()
    assert body["enqueued_at"] is not None
    assert body["started_at"] is None
    assert body["ended_at"] is None


def test_list_jobs_returns_empty_when_no_jobs(client):
    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json() == {"jobs": []}


def test_list_jobs_spans_queued_started_finished_failed(client, fake_queue, fake_redis_conn):
    queued_job = fake_queue.enqueue(TASK_VALIDATE_MODEL, "tiny")

    started_job = fake_queue.enqueue(TASK_VALIDATE_MODEL, "base")
    fake_queue.started_job_registry.add(started_job, ttl=500)
    started_job.set_status(JobStatus.STARTED)

    finished_job = Job.create(func=TASK_VALIDATE_MODEL, args=("small",), connection=fake_redis_conn)
    finished_job.save()
    fake_queue.finished_job_registry.add(finished_job, ttl=500)
    finished_job.set_status(JobStatus.FINISHED)

    failed_job = Job.create(func=TASK_VALIDATE_MODEL, args=("medium",), connection=fake_redis_conn)
    failed_job.save()
    fake_queue.failed_job_registry.add(failed_job, ttl=500)
    failed_job.set_status(JobStatus.FAILED)

    response = client.get("/api/jobs")

    assert response.status_code == 200
    body = response.json()
    returned_ids = {job["job_id"] for job in body["jobs"]}
    assert returned_ids == {queued_job.id, started_job.id, finished_job.id, failed_job.id}


def test_list_jobs_respects_limit(client, fake_queue):
    for i in range(5):
        fake_queue.enqueue(TASK_VALIDATE_MODEL, f"size-{i}")

    response = client.get("/api/jobs?limit=2")

    assert response.status_code == 200
    assert len(response.json()["jobs"]) == 2


def test_list_jobs_sorted_most_recent_first(client, fake_queue):
    older = fake_queue.enqueue(TASK_VALIDATE_MODEL, "tiny")
    newer = fake_queue.enqueue(TASK_VALIDATE_MODEL, "base")
    newer.enqueued_at = older.enqueued_at.replace(year=older.enqueued_at.year + 1)
    newer.save()

    response = client.get("/api/jobs")

    body = response.json()
    assert [job["job_id"] for job in body["jobs"]] == [newer.id, older.id]
