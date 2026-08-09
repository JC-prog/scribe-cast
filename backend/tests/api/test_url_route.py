def test_transcribe_url_enqueues_job(client, fake_queue):
    response = client.post(
        "/api/url/transcribe",
        json={"url": "https://www.youtube.com/watch?v=abc123", "model_size": "tiny", "language": "auto"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert fake_queue.count == 1


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
