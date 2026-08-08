import time
from dataclasses import dataclass


@dataclass
class Stopwatch:
    elapsed_ms: float = 0.0
    _start: float = 0.0

    def __enter__(self) -> "Stopwatch":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
