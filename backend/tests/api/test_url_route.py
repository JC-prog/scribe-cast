from rq.job import Job


def test_transcribe_url_enqueues_job(client, fake_queue):
    response = client.post(
        "/api/url/transcribe",
        json={"url": "https://www.youtube.com/watch?v=abc123", "model_size": "tiny", "language": "auto"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert fake_queue.count == 1


def test_transcribe_url_defaults_translate_to_false(client, fake_queue, fake_redis_conn):
    response = client.post(
        "/api/url/transcribe",
        json={"url": "https://www.youtube.com/watch?v=abc123", "model_size": "tiny", "language": "auto"},
    )

    job = Job.fetch(response.json()["job_id"], connection=fake_redis_conn)
    assert job.args[-1] is False


def test_transcribe_url_passes_translate_through(client, fake_queue, fake_redis_conn):
    response = client.post(
        "/api/url/transcribe",
        json={
            "url": "https://www.youtube.com/watch?v=abc123",
            "model_size": "tiny",
            "language": "es",
            "translate": True,
        },
    )

    job = Job.fetch(response.json()["job_id"], connection=fake_redis_conn)
    assert job.args[-1] is True


def test_transcribe_url_rejects_malformed_url(client):
    response = client.post(
        "/api/url/transcribe",
        json={"url": "not-a-url", "model_size": "tiny", "language": "auto"},
    )

    assert response.status_code == 422


def test_transcribe_url_rejects_unknown_model_size(client):
    response = client.post(
        "/api/url/transcribe",
        json={"url": "https://www.youtube.com/watch?v=abc123", "model_size": "not-a-real-size", "language": "auto"},
    )

    assert response.status_code == 400


def test_transcribe_url_rejects_unknown_language(client):
    response = client.post(
        "/api/url/transcribe",
        json={
            "url": "https://www.youtube.com/watch?v=abc123",
            "model_size": "tiny",
            "language": "not-a-real-language",
        },
    )

    assert response.status_code == 400
