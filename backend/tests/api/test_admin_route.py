import pytest

from app.core import runtime_settings as runtime_settings_module


@pytest.fixture(autouse=True)
def patch_admin_redis(monkeypatch, fake_redis_conn):
    monkeypatch.setattr(runtime_settings_module, "_redis_conn", None)
    monkeypatch.setattr(runtime_settings_module, "_get_redis_conn", lambda: fake_redis_conn)


def test_get_settings_returns_defaults_initially(client):
    response = client.get("/api/admin/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["batch_size"] == 16
    assert body["chunk_size"] == 30
    assert body["vad_method"] == "silero"
    assert body["max_chars_per_cue"] == 84
    assert body["max_seconds_per_cue"] == 7.0
    assert body["hf_token_set"] is False
    assert "hf_token" not in body


def test_patch_settings_persists_and_is_reflected_on_get(client):
    response = client.patch("/api/admin/settings", json={"batch_size": 32, "chunk_size": 10})

    assert response.status_code == 200
    assert response.json()["batch_size"] == 32

    followup = client.get("/api/admin/settings")
    assert followup.json()["batch_size"] == 32
    assert followup.json()["chunk_size"] == 10


def test_patch_settings_rejects_out_of_range_values(client):
    response = client.patch("/api/admin/settings", json={"batch_size": 0})

    assert response.status_code == 422


def test_patch_settings_never_echoes_raw_hf_token(client):
    response = client.patch("/api/admin/settings", json={"vad_method": "pyannote", "hf_token": "hf_secret"})

    assert response.status_code == 200
    body = response.json()
    assert "hf_token" not in body
    assert body["hf_token_set"] is True


def test_patch_settings_omitting_hf_token_leaves_it_set(client):
    client.patch("/api/admin/settings", json={"hf_token": "hf_secret"})

    response = client.patch("/api/admin/settings", json={"batch_size": 8})

    assert response.json()["hf_token_set"] is True


def test_patch_settings_empty_string_clears_hf_token(client):
    client.patch("/api/admin/settings", json={"hf_token": "hf_secret"})

    response = client.patch("/api/admin/settings", json={"hf_token": ""})

    assert response.json()["hf_token_set"] is False


def test_reset_restores_defaults(client):
    client.patch("/api/admin/settings", json={"batch_size": 99})

    response = client.post("/api/admin/settings/reset")

    assert response.status_code == 200
    assert response.json()["batch_size"] == 16

    followup = client.get("/api/admin/settings")
    assert followup.json()["batch_size"] == 16
