from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_get_languages_includes_auto_detect_first():
    response = client.get("/api/languages")

    assert response.status_code == 200
    body = response.json()
    assert body["languages"][0] == {"code": "auto", "label": "Auto-detect"}
    codes = [entry["code"] for entry in body["languages"]]
    assert "en" in codes
    assert len(codes) == len(set(codes))
