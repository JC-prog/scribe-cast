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
