import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger("scribecast.device")

DeviceRequest = Literal["auto", "cuda", "cpu"]

_DEFAULT_COMPUTE_TYPE = {"cuda": "float16", "cpu": "int8"}


@dataclass
class DeviceResolution:
    device: Literal["cuda", "cpu"]
    compute_type: str
    fallback_occurred: bool


def _cuda_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        # Missing/broken CUDA libraries, no driver, etc. Treat as "no GPU".
        return False


def resolve_device(requested: DeviceRequest, compute_type_override: str | None = None) -> DeviceResolution:
    """
    Decide the actual (device, compute_type) to use, given a requested mode.

    - "cpu": always CPU.
    - "cuda": use GPU if actually usable, else fall back to CPU with fallback_occurred=True.
    - "auto": use GPU if available, else CPU (no fallback flag, since CPU was an acceptable outcome).
    """
    fallback_occurred = False

    if requested == "cpu":
        device: Literal["cuda", "cpu"] = "cpu"
    elif requested == "cuda":
        if _cuda_available():
            device = "cuda"
        else:
            logger.warning("event=device_fallback requested=cuda reason=cuda_unavailable resolved=cpu")
            device = "cpu"
            fallback_occurred = True
    else:  # auto
        device = "cuda" if _cuda_available() else "cpu"

    compute_type = compute_type_override or _DEFAULT_COMPUTE_TYPE[device]
    return DeviceResolution(device=device, compute_type=compute_type, fallback_occurred=fallback_occurred)
