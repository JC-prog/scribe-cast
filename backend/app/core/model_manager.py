import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass

import whisperx

from app.config import settings
from app.core.device import DeviceRequest, resolve_device
from app.logging_config import get_logger, log_event
from app.utils.timing import Stopwatch

logger = get_logger("scribecast.model_manager")

CacheKey = tuple[str, str, str]  # (model_size, device, compute_type)
AlignCacheKey = tuple[str, str]  # (language, device)


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
        cache_key: CacheKey = (model_size, resolution.device, resolution.compute_type)

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

            with Stopwatch() as stopwatch:
                # vad_method="silero" is deliberate: whisperx defaults to a
                # gated pyannote VAD model requiring a Hugging Face token.
                # Silero is ungated and fully local - keeps the "no HF
                # account needed" property of the core transcription path.
                model = whisperx.load_model(
                    model_size,
                    resolution.device,
                    compute_type=resolution.compute_type,
                    vad_method="silero",
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
