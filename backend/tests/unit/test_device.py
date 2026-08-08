from app.core import device as device_module
from app.core.device import resolve_device


def test_cpu_requested_never_checks_cuda(monkeypatch):
    called = False

    def fake_cuda_available():
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(device_module, "_cuda_available", fake_cuda_available)

    result = resolve_device("cpu")

    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.fallback_occurred is False
    assert called is False


def test_cuda_requested_and_available(monkeypatch):
    monkeypatch.setattr(device_module, "_cuda_available", lambda: True)

    result = resolve_device("cuda")

    assert result.device == "cuda"
    assert result.compute_type == "float16"
    assert result.fallback_occurred is False


def test_cuda_requested_but_unavailable_falls_back_to_cpu(monkeypatch):
    monkeypatch.setattr(device_module, "_cuda_available", lambda: False)

    result = resolve_device("cuda")

    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.fallback_occurred is True


def test_auto_picks_gpu_when_available(monkeypatch):
    monkeypatch.setattr(device_module, "_cuda_available", lambda: True)

    result = resolve_device("auto")

    assert result.device == "cuda"
    assert result.fallback_occurred is False


def test_auto_picks_cpu_when_unavailable(monkeypatch):
    monkeypatch.setattr(device_module, "_cuda_available", lambda: False)

    result = resolve_device("auto")

    assert result.device == "cpu"
    assert result.fallback_occurred is False


def test_compute_type_override_respected(monkeypatch):
    monkeypatch.setattr(device_module, "_cuda_available", lambda: True)

    result = resolve_device("cuda", compute_type_override="int8_float16")

    assert result.compute_type == "int8_float16"
