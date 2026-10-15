"""Tiny in-memory, per-process rate limiter and click de-duplicator.

Good enough for a single-process deployment; swap for a shared store (Redis)
if the API is ever run with multiple workers.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from .config import get_settings


class RateLimiter:
    def __init__(self) -> None:
        self.enabled = get_settings().rate_limit_enabled
        self._hits: dict[tuple, deque[float]] = defaultdict(deque)
        self._seen: dict[tuple, float] = {}

    def reset(self) -> None:
        self._hits.clear()
        self._seen.clear()

    def allow(self, key: tuple, limit: int, window_seconds: float) -> bool:
        if not self.enabled:
            return True
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True

    def first_seen(self, key: tuple, window_seconds: float) -> bool:
        """True if `key` has not been seen in the last `window_seconds`; records it."""
        if not self.enabled:
            return True
        now = time.monotonic()
        if len(self._seen) > 10_000:
            self._seen = {k: t for k, t in self._seen.items() if now - t < window_seconds}
        last = self._seen.get(key)
        if last is not None and now - last < window_seconds:
            return False
        self._seen[key] = now
        return True


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, limit: int, window_seconds: float):
    """FastAPI dependency factory: 429 once an IP exceeds `limit` calls per window."""

    def dependency(request: Request) -> None:
        if not limiter.allow((name, client_ip(request)), limit, window_seconds):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests. Please slow down.")

    return dependency
