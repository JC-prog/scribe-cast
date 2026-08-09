import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass

import whisperx

from app.config import settings
from app.core.device import DeviceRequest, resolve_device
from app.core.runtime_settings import load_runtime_settings
from app.logging_config import get_logger, log_event
from app.utils.timing import Stopwatch

logger = get_logger("scribecast.model_manager")

# (model_size, device, compute_type, settings_fingerprint) - the fingerprint
# covers whatever RuntimeSettings fields affect whisperx.load_model()'s
# construction (vad_method, beam_size, temperature,
# condition_on_previous_text), so a settings change naturally invalidates a
# warm cache entry instead of it silently keeping stale behavior.
CacheKey = tuple[str, str, str, tuple]
AlignCacheKey = tuple[str, str]  # (language, device)


def _settings_fingerprint(runtime_settings) -> tuple:
    return (
        runtime_settings.vad_method,
        runtime_settings.beam_size,
        runtime_settings.temperature,
        runtime_settings.condition_on_previous_text,
    )


@dataclass
class ValidationResult:
    ok: bool
    device_used: str | None
    fallback_occurred: bool
    load_time_ms: float | None
    error: str | None


class ModelManager:
    """
    Caches loaded WhisperX ASR pipelines and alignment models so repeated
    jobs don't pay the (slow) load cost more than once. Intended to live in
    a single, non-forking worker process (see rq_worker.py) — the cache is
    useless if RQ forks a fresh process per job.

    Two separate caches: ASR models are keyed by (model_size, device,
    compute_type), alignment (wav2vec2) models are keyed by (language,
    device) - they're loaded on different axes, so one cache can't serve
    both.
    """

    def __init__(self, max_cached_models: int = 1):
        self._max_cached_models = max_cached_models
        self._cache: "OrderedDict[CacheKey, whisperx.asr.FasterWhisperPipeline]" = OrderedDict()
        self._align_cache: "OrderedDict[AlignCacheKey, tuple]" = OrderedDict()
        self._lock = threading.Lock()

    def load(self, model_size: str, device_request: DeviceRequest = "auto") -> tuple:
        resolution = resolve_device(device_request, compute_type_override=settings.compute_type)
        runtime_settings = load_runtime_settings()
        cache_key: CacheKey = (
            model_size,
            resolution.device,
            resolution.compute_type,
            _settings_fingerprint(runtime_settings),
        )

        with self._lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                model = self._cache[cache_key]
                return model, {
                    "device_used": resolution.device,
                    "compute_type": resolution.compute_type,
                    "fallback_occurred": resolution.fallback_occurred,
                    "load_time_ms": 0.0,
                    "cache_hit": True,
                }

            asr_options = {}
            if runtime_settings.beam_size is not None:
                asr_options["beam_size"] = runtime_settings.beam_size
            if runtime_settings.temperature is not None:
                asr_options["temperature"] = runtime_settings.temperature
            if runtime_settings.condition_on_previous_text is not None:
                asr_options["condition_on_previous_text"] = runtime_settings.condition_on_previous_text

            with Stopwatch() as stopwatch:
                # vad_method defaults to "silero" (see RuntimeSettings) as
                # the lower-friction choice. Note: verified against a real
                # run that in whisperx 3.8.6, "pyannote" VAD actually loads
                # its checkpoint bundled in the whisperx package itself
                # (whisperx/assets/pytorch_model.bin), not a live gated HF
                # download - use_auth_token had no effect on VAD in that
                # test (a bogus token still loaded fine). Still passed
                # through here since that's an implementation detail of the
                # currently-pinned whisperx version, not a documented
                # contract - a future version, or other pyannote-gated
                # features (e.g. diarization, not implemented here), may
                # depend on it for real.
                model = whisperx.load_model(
                    model_size,
                    resolution.device,
                    compute_type=resolution.compute_type,
                    vad_method=runtime_settings.vad_method,
                    asr_options=asr_options or None,
                    use_auth_token=runtime_settings.hf_token if runtime_settings.vad_method == "pyannote" else None,
                    download_root=str(settings.model_cache_dir),
                )

            self._cache[cache_key] = model
            while len(self._cache) > self._max_cached_models:
                self._cache.popitem(last=False)

            log_event(
                logger,
                "model_load",
                model=model_size,
                device=resolution.device,
                compute_type=resolution.compute_type,
                vad_method=runtime_settings.vad_method,
                duration_ms=round(stopwatch.elapsed_ms, 1),
                fallback_occurred=resolution.fallback_occurred,
            )

            return model, {
                "device_used": resolution.device,
                "compute_type": resolution.compute_type,
                "fallback_occurred": resolution.fallback_occurred,
                "load_time_ms": stopwatch.elapsed_ms,
                "cache_hit": False,
            }

    def load_align_model(self, language: str, device: str) -> tuple:
        cache_key: AlignCacheKey = (language, device)

        with self._lock:
            if cache_key in self._align_cache:
                self._align_cache.move_to_end(cache_key)
                return self._align_cache[cache_key]

            with Stopwatch() as stopwatch:
                align_model, metadata = whisperx.load_align_model(language_code=language, device=device)

            self._align_cache[cache_key] = (align_model, metadata)
            while len(self._align_cache) > self._max_cached_models:
                self._align_cache.popitem(last=False)

            log_event(
                logger,
                "align_model_load",
                language=language,
                device=device,
                duration_ms=round(stopwatch.elapsed_ms, 1),
            )

            return align_model, metadata

    def validate(self, model_size: str, device_request: DeviceRequest = "auto") -> ValidationResult:
        try:
            _, info = self.load(model_size, device_request)
            return ValidationResult(
                ok=True,
                device_used=info["device_used"],
                fallback_occurred=info["fallback_occurred"],
                load_time_ms=info["load_time_ms"],
                error=None,
            )
        except (RuntimeError, OSError, ValueError) as exc:
            log_event(logger, "model_load_failed", level=logging.ERROR, model=model_size, error=str(exc))
            return ValidationResult(
                ok=False, device_used=None, fallback_occurred=False, load_time_ms=None, error=str(exc)
            )
        except Exception as exc:  # noqa: BLE001 - validate() must never raise
            log_event(logger, "model_load_failed", level=logging.ERROR, model=model_size, error=str(exc))
            return ValidationResult(
                ok=False, device_used=None, fallback_occurred=False, load_time_ms=None, error=str(exc)
            )


_manager: ModelManager | None = None


def get_model_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager(max_cached_models=settings.max_cached_models)
    return _manager
