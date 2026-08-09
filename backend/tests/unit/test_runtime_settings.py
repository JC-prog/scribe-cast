import fakeredis
import pytest

from app.core import runtime_settings as runtime_settings_module
from app.core.runtime_settings import load_runtime_settings, reset_runtime_settings, save_runtime_settings
from app.schemas.runtime_settings import RuntimeSettings, RuntimeSettingsUpdate


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    conn = fakeredis.FakeStrictRedis()
    monkeypatch.setattr(runtime_settings_module, "_redis_conn", None)
    monkeypatch.setattr(runtime_settings_module, "_get_redis_conn", lambda: conn)
    return conn


def test_load_returns_defaults_when_nothing_stored():
    result = load_runtime_settings()

    assert result == RuntimeSettings()


def test_load_falls_back_to_defaults_on_corrupt_json(fake_redis):
    fake_redis.set(runtime_settings_module.REDIS_KEY, b"not valid json")

    result = load_runtime_settings()

    assert result == RuntimeSettings()


def test_save_and_load_round_trip():
    save_runtime_settings(RuntimeSettingsUpdate(batch_size=32, chunk_size=15))

    result = load_runtime_settings()

    assert result.batch_size == 32
    assert result.chunk_size == 15
    assert result.max_chars_per_cue == 84  # untouched fields keep their default


def test_save_only_updates_fields_that_were_sent():
    save_runtime_settings(RuntimeSettingsUpdate(batch_size=32))
    save_runtime_settings(RuntimeSettingsUpdate(chunk_size=15))  # should not reset batch_size

    result = load_runtime_settings()

    assert result.batch_size == 32
    assert result.chunk_size == 15


def test_save_omitting_hf_token_leaves_it_unchanged():
    save_runtime_settings(RuntimeSettingsUpdate(hf_token="secret-token"))
    save_runtime_settings(RuntimeSettingsUpdate(batch_size=64))  # hf_token not sent this time

    result = load_runtime_settings()

    assert result.hf_token == "secret-token"
    assert result.batch_size == 64


def test_save_empty_string_clears_hf_token():
    save_runtime_settings(RuntimeSettingsUpdate(hf_token="secret-token"))
    save_runtime_settings(RuntimeSettingsUpdate(hf_token=""))

    result = load_runtime_settings()

    assert result.hf_token == ""


def test_reset_restores_defaults():
    save_runtime_settings(RuntimeSettingsUpdate(batch_size=99))

    reset_runtime_settings()

    assert load_runtime_settings() == RuntimeSettings()
