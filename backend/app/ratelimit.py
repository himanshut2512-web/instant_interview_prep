"""In-process sliding-window rate limiter for the sign-in endpoints.

It protects against password guessing and email flooding on a single server
process. Behind several workers or servers, each keeps its own counts.
"""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def retry_after(self, key: str, limit: int, window: float) -> int:
        """Seconds until `key` may try again (0 = allowed now). Does not record a hit."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits.get(key)
            if not hits:
                return 0
            while hits and hits[0] <= now - window:
                hits.popleft()
            if len(hits) < limit:
                return 0
            return max(1, int(hits[0] + window - now) + 1)

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._hits.setdefault(key, deque()).append(now)
            if now - self._last_sweep > 300:
                self._sweep(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def _sweep(self, now: float, horizon: float = 3600) -> None:
        for key in [k for k, v in self._hits.items() if not v or v[-1] < now - horizon]:
            del self._hits[key]
        self._last_sweep = now
