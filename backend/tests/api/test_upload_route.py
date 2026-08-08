from app.api.routes import upload as upload_route_module


def test_upload_video_enqueues_job_and_writes_file(client, fake_queue, tmp_path, monkeypatch):
    monkeypatch.setattr(upload_route_module.settings, "uploads_dir", tmp_path / "uploads")

    response = client.post(
        "/api/upload",
        files={"file": ("video.mp4", b"fake video bytes", "video/mp4")},
        data={"model_size": "tiny", "language": "auto"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert fake_queue.count == 1

    uploaded_files = list((tmp_path / "uploads").iterdir())
    assert len(uploaded_files) == 1
    assert uploaded_files[0].read_bytes() == b"fake video bytes"


def test_upload_video_rejects_unknown_model_size(client, tmp_path, monkeypatch):
    monkeypatch.setattr(upload_route_module.settings, "uploads_dir", tmp_path / "uploads")

    response = client.post(
        "/api/upload",
        files={"file": ("video.mp4", b"data", "video/mp4")},
        data={"model_size": "not-a-real-size", "language": "auto"},
    )

    assert response.status_code == 400


def test_upload_video_rejects_unknown_language(client, tmp_path, monkeypatch):
    monkeypatch.setattr(upload_route_module.settings, "uploads_dir", tmp_path / "uploads")

    response = client.post(
        "/api/upload",
        files={"file": ("video.mp4", b"data", "video/mp4")},
        data={"model_size": "tiny", "language": "not-a-real-language"},
    )

    assert response.status_code == 400
