from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_models_returns_catalog():
    response = client.get("/api/models")

    assert response.status_code == 200
    body = response.json()
    sizes = [m["size"] for m in body["models"]]
    assert "tiny" in sizes
    assert "large-v3" in sizes
    assert all({"size", "label", "hint"} <= m.keys() for m in body["models"])


def test_validate_model_enqueues_job(client, fake_queue):
    response = client.post("/api/models/validate", json={"model_size": "tiny"})

    assert response.status_code == 200
    assert "job_id" in response.json()
    assert fake_queue.count == 1


def test_validate_model_rejects_unknown_size(client, fake_queue):
    response = client.post("/api/models/validate", json={"model_size": "not-a-real-size"})

    assert response.status_code == 400
    assert fake_queue.count == 0
