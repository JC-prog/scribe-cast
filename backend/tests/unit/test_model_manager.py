import pytest

from app.core import model_manager as model_manager_module
from app.core.model_manager import ModelManager
from app.schemas.runtime_settings import RuntimeSettings


def _patch_runtime_settings(monkeypatch, **overrides):
    rs = RuntimeSettings(**overrides)
    monkeypatch.setattr(model_manager_module, "load_runtime_settings", lambda: rs)
    return rs


class FakeWhisperXModel:
    instances_created = 0

    def __init__(self, model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
        FakeWhisperXModel.instances_created += 1
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type


def fake_load_model(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
    return FakeWhisperXModel(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root)


@pytest.fixture(autouse=True)
def reset_fake_model_counter():
    FakeWhisperXModel.instances_created = 0
    yield


def test_load_instantiates_model_on_cache_miss(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager(max_cached_models=1)

    model, info = manager.load("tiny", device_request="cpu")

    assert isinstance(model, FakeWhisperXModel)
    assert info["cache_hit"] is False
    assert info["device_used"] == "cpu"
    assert FakeWhisperXModel.instances_created == 1


def test_load_uses_silero_vad_by_default(monkeypatch):
    captured = {}

    def capturing_load_model(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
        captured["vad_method"] = vad_method
        captured["use_auth_token"] = use_auth_token
        return FakeWhisperXModel(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root)

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", capturing_load_model)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")

    assert captured["vad_method"] == "silero"
    assert captured["use_auth_token"] is None  # never sent when not using pyannote


def test_load_passes_pyannote_vad_and_token_when_configured(monkeypatch):
    captured = {}

    def capturing_load_model(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
        captured["vad_method"] = vad_method
        captured["use_auth_token"] = use_auth_token
        return FakeWhisperXModel(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root)

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", capturing_load_model)
    _patch_runtime_settings(monkeypatch, vad_method="pyannote", hf_token="hf_secret_token")
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")

    assert captured["vad_method"] == "pyannote"
    assert captured["use_auth_token"] == "hf_secret_token"


def test_load_only_sets_asr_options_that_are_configured(monkeypatch):
    captured = {}

    def capturing_load_model(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
        captured["asr_options"] = asr_options
        return FakeWhisperXModel(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root)

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", capturing_load_model)
    _patch_runtime_settings(monkeypatch)  # all None -> nothing configured
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")

    assert captured["asr_options"] is None


def test_load_sets_configured_asr_options(monkeypatch):
    captured = {}

    def capturing_load_model(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root):
        captured["asr_options"] = asr_options
        return FakeWhisperXModel(model_size, device, compute_type, vad_method, asr_options, use_auth_token, download_root)

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", capturing_load_model)
    _patch_runtime_settings(monkeypatch, beam_size=3, temperature=0.2, condition_on_previous_text=True)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")

    assert captured["asr_options"] == {"beam_size": 3, "temperature": 0.2, "condition_on_previous_text": True}


def test_load_reuses_cached_model(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    model, info = manager.load("tiny", device_request="cpu")

    assert info["cache_hit"] is True
    assert FakeWhisperXModel.instances_created == 1


def test_load_evicts_lru_when_over_capacity(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager(max_cached_models=1)

    manager.load("tiny", device_request="cpu")
    manager.load("base", device_request="cpu")  # evicts "tiny"
    _, info = manager.load("tiny", device_request="cpu")  # must reload

    assert info["cache_hit"] is False
    assert FakeWhisperXModel.instances_created == 3  # tiny, base, tiny-again (evicted)


def test_settings_change_busts_the_cache(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    manager = ModelManager(max_cached_models=2)

    _patch_runtime_settings(monkeypatch, beam_size=5)
    manager.load("tiny", device_request="cpu")

    _patch_runtime_settings(monkeypatch, beam_size=10)  # different construction-time setting
    _, info = manager.load("tiny", device_request="cpu")

    assert info["cache_hit"] is False
    assert FakeWhisperXModel.instances_created == 2


def test_validate_returns_ok_result(monkeypatch):
    monkeypatch.setattr(model_manager_module.whisperx, "load_model", fake_load_model)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager()

    result = manager.validate("tiny", device_request="cpu")

    assert result.ok is True
    assert result.error is None
    assert result.device_used == "cpu"


def test_validate_catches_runtime_error_without_raising(monkeypatch):
    def raise_runtime_error(*args, **kwargs):
        raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", raise_runtime_error)
    _patch_runtime_settings(monkeypatch)
    manager = ModelManager()

    result = manager.validate("large-v3", device_request="cpu")

    assert result.ok is False
    assert "CUDA out of memory" in result.error


def test_validate_catches_missing_weights_error(monkeypatch):
    def raise_os_error(*args, **kwargs):
        raise OSError("model weights not found")

    monkeypatch.setattr(model_manager_module.whisperx, "load_model", raise_os_error)
    _patch_runtime_settings(monkeypatch)
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
