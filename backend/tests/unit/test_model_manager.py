import pytest

from app.core import model_manager as model_manager_module
from app.core.model_manager import ModelManager


class FakeWhisperXModel:
    instances_created = 0

    def __init__(self, model_size, device, compute_type, vad_method, download_root):
        FakeWhisperXModel.instances_created += 1
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type


def fake_load_model(model_size, device, compute_type, vad_method, download_root):
    return FakeWhisperXModel(model_size, device, compute_type, vad_method, download_root)


@pytest.fixture(autouse=True)
def reset_fake_model_counter():
    FakeWhisperXModel.instances_created = 0
    yield


def test_load_instantiates_model_on_cache_miss(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    manager = ModelManager(max_cached_models=1)

    model, info = manager.load("tiny", device_request="cpu")

    assert isinstance(model, FakeWhisperXModel)
    assert info["cache_hit"] is False
    assert info["device_used"] == "cpu"
    assert FakeWhisperXModel.instances_created == 1


def test_load_uses_silero_vad_to_avoid_gated_pyannote_default(monkeypatch):
    captured = {}

    def capturing_load_model(model_size, device, compute_type, vad_method, download_root):
        captured["vad_method"] = vad_method
        return FakeWhisperXModel(model_size, device, compute_type, vad_method, download_root)

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", capturing_load_model)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")

    assert captured["vad_method"] == "silero"


def test_load_reuses_cached_model(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    model, info = manager.load("tiny", device_request="cpu")

    assert info["cache_hit"] is True
    assert FakeWhisperXModel.instances_created == 1


def test_load_evicts_lru_when_over_capacity(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    manager.load("base", device_request="cpu")  # evicts "tiny"
    _, info = manager.load("tiny", device_request="cpu")  # must reload

    assert info["cache_hit"] is False
    assert FakeWhisperXModel.instances_created == 3  # tiny, base, tiny-again (evicted)


def test_validate_returns_ok_result(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    manager = ModelManager()

    result = manager.validate("tiny", device_request="cpu")

    assert result.ok is True
    assert result.error is None
    assert result.device_used == "cpu"


def test_validate_catches_runtime_error_without_raising(monkeypatch):
    def raise_runtime_error(*args, **kwargs):
        raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", raise_runtime_error)
    manager = ModelManager()

    result = manager.validate("large-v3", device_request="cpu")

    assert result.ok is False
    assert "CUDA out of memory" in result.error


def test_validate_catches_missing_weights_error(monkeypatch):
    def raise_os_error(*args, **kwargs):
        raise OSError("model weights not found")

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", raise_os_error)
    manager = ModelManager()

    result = manager.validate("tiny", device_request="cpu")

    assert result.ok is False
    assert "not found" in result.error


def test_load_align_model_instantiates_on_cache_miss(monkeypatch):
    calls = []

    def fake_load_align_model(language_code, device):
        calls.append((language_code, device))
        return "align-model", {"meta": True}

    monkeypatch.setattr(model_manager_module.whisperx, "load_align_model", fake_load_align_model)
    manager = ModelManager(max_cached_models=1)

    model_a, metadata = manager.load_align_model("en", "cpu")

    assert model_a == "align-model"
    assert metadata == {"meta": True}
    assert calls == [("en", "cpu")]


def test_load_align_model_reuses_cache(monkeypatch):
    calls = []

    def fake_load_align_model(language_code, device):
        calls.append((language_code, device))
        return "align-model", {}

    monkeypatch.setattr(model_manager_module.whisperx, "load_align_model", fake_load_align_model)
    manager = ModelManager(max_cached_models=1)

    manager.load_align_model("en", "cpu")
    manager.load_align_model("en", "cpu")

    assert len(calls) == 1


def test_load_align_model_evicts_lru_when_over_capacity(monkeypatch):
    calls = []

    def fake_load_align_model(language_code, device):
        calls.append((language_code, device))
        return f"align-model-{language_code}", {}

    monkeypatch.setattr(model_manager_module.whisperx, "load_align_model", fake_load_align_model)
    manager = ModelManager(max_cached_models=1)

    manager.load_align_model("en", "cpu")
    manager.load_align_model("fr", "cpu")  # evicts "en"
    manager.load_align_model("en", "cpu")  # must reload

    assert len(calls) == 3
