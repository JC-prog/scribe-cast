from rq.job import Job, JobStatus

from app.worker.task_names import TASK_TRANSCRIBE_UPLOAD


def test_download_not_found_for_unknown_job(client):
    response = client.get("/api/download/does-not-exist")
    assert response.status_code == 404


def test_download_not_found_for_unfinished_job(client, fake_queue):
    job = fake_queue.enqueue(TASK_TRANSCRIBE_UPLOAD, "upload.mp4", "video.mp4", "tiny", None)

    response = client.get(f"/api/download/{job.id}")

    assert response.status_code == 404


def test_download_returns_srt_file_for_finished_job(client, fake_redis_conn, tmp_path):
    srt_path = tmp_path / "video.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")

    job = Job.create(
        func=TASK_TRANSCRIBE_UPLOAD,
        args=("upload.mp4", "video.mp4", "tiny", None),
        connection=fake_redis_conn,
        meta={"output_path": str(srt_path)},
    )
    job.save()
    job.set_status(JobStatus.FINISHED)

    response = client.get(f"/api/download/{job.id}")

    assert response.status_code == 200
    assert response.content == srt_path.read_bytes()
    assert "video.srt" in response.headers["content-disposition"]


def test_download_not_found_when_file_missing(client, fake_redis_conn, tmp_path):
    missing_path = tmp_path / "gone.srt"

    job = Job.create(
        func=TASK_TRANSCRIBE_UPLOAD,
        args=("upload.mp4", "video.mp4", "tiny", None),
        connection=fake_redis_conn,
        meta={"output_path": str(missing_path)},
    )
    job.save()
    job.set_status(JobStatus.FINISHED)

    response = client.get(f"/api/download/{job.id}")

    assert response.status_code == 404
