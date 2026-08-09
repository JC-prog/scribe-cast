from fastapi.testclient import TestClient

from app.api.main import app
from app.config import settings

client = TestClient(app)


def test_get_version_returns_configured_version(monkeypatch):
    monkeypatch.setattr(settings, "app_version", "9.9.9")

    response = client.get("/api/version")

    assert response.status_code == 200
    assert response.json() == {"version": "9.9.9"}
