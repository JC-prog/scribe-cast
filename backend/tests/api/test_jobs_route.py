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
