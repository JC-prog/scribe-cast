import json


def _touch(path, content=b"fake"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_scan_returns_discovered_videos(client, tmp_path):
    _touch(tmp_path / "video.mp4")
    _touch(tmp_path / "notes.txt")

    response = client.post("/api/folder/scan", json={"folder_path": str(tmp_path)})

    assert response.status_code == 200
    videos = response.json()["videos"]
    assert len(videos) == 1
    assert videos[0]["relative_path"] == "video.mp4"


def test_scan_returns_400_for_missing_folder(client, tmp_path):
    response = client.post("/api/folder/scan", json={"folder_path": str(tmp_path / "nope")})

    assert response.status_code == 400


def test_transcribe_enqueues_jobs_and_stores_batch(client, fake_queue, fake_redis_conn, tmp_path):
    video_a = tmp_path / "a.mp4"
    video_b = tmp_path / "b.mp4"
    _touch(video_a)
    _touch(video_b)

    response = client.post(
        "/api/folder/transcribe",
        json={
            "folder_path": str(tmp_path),
            "video_paths": [str(video_a), str(video_b)],
            "model_size": "tiny",
            "language": "auto",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["job_ids"]) == 2
    assert fake_queue.count == 2

    stored = json.loads(fake_redis_conn.get(f"batch:{body['batch_id']}"))
    assert stored == body["job_ids"]


def test_transcribe_rejects_path_outside_root(client, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside_video = tmp_path / "outside.mp4"
    _touch(outside_video)

    response = client.post(
        "/api/folder/transcribe",
        json={
            "folder_path": str(root),
            "video_paths": [str(outside_video)],
            "model_size": "tiny",
            "language": "auto",
        },
    )

    assert response.status_code == 400


def test_transcribe_rejects_unknown_model_size(client, tmp_path):
    video_a = tmp_path / "a.mp4"
    _touch(video_a)

    response = client.post(
        "/api/folder/transcribe",
        json={
            "folder_path": str(tmp_path),
            "video_paths": [str(video_a)],
            "model_size": "bogus",
            "language": "auto",
        },
    )

    assert response.status_code == 400
