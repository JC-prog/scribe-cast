import pytest

from app.core import model_manager as model_manager_module
from app.core.model_manager import ModelManager


class FakeWhisperModel:
    instances_created = 0

    def __init__(self, model_size, device, compute_type, download_root):
        FakeWhisperModel.instances_created += 1
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type


@pytest.fixture(autouse=True)
def reset_fake_model_counter():
    FakeWhisperModel.instances_created = 0
    yield


def test_load_instantiates_model_on_cache_miss(monkeypatch):
    monkeypatch.setattr(model_manager_module, "WhisperModel", FakeWhisperModel)
    manager = ModelManager(max_cached_models=1)

    model, info = manager.load("tiny", device_request="cpu")

    assert isinstance(model, FakeWhisperModel)
    assert info["cache_hit"] is False
    assert info["device_used"] == "cpu"
    assert FakeWhisperModel.instances_created == 1


def test_load_reuses_cached_model(monkeypatch):
    monkeypatch.setattr(model_manager_module, "WhisperModel", FakeWhisperModel)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    model, info = manager.load("tiny", device_request="cpu")

    assert info["cache_hit"] is True
    assert FakeWhisperModel.instances_created == 1


def test_load_evicts_lru_when_over_capacity(monkeypatch):
    monkeypatch.setattr(model_manager_module, "WhisperModel", FakeWhisperModel)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    manager.load("base", device_request="cpu")  # evicts "tiny"
    _, info = manager.load("tiny", device_request="cpu")  # must reload

    assert info["cache_hit"] is False
    assert FakeWhisperModel.instances_created == 3  # tiny, base, tiny-again (evicted)


def test_validate_returns_ok_result(monkeypatch):
    monkeypatch.setattr(model_manager_module, "WhisperModel", FakeWhisperModel)
    manager = ModelManager()

    result = manager.validate("tiny", device_request="cpu")

    assert result.ok is True
    assert result.error is None
    assert result.device_used == "cpu"


def test_validate_catches_runtime_error_without_raising(monkeypatch):
    def raise_runtime_error(*args, **kwargs):
        raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(model_manager_module, "WhisperModel", raise_runtime_error)
    manager = ModelManager()

    result = manager.validate("large-v3", device_request="cpu")

    assert result.ok is False
    assert "CUDA out of memory" in result.error


def test_validate_catches_missing_weights_error(monkeypatch):
    def raise_os_error(*args, **kwargs):
        raise OSError("model weights not found")

    monkeypatch.setattr(model_manager_module, "WhisperModel", raise_os_error)
    manager = ModelManager()

    result = manager.validate("tiny", device_request="cpu")

    assert result.ok is False
    assert "not found" in result.error
